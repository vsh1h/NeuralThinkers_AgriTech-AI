from typing import List, Dict, Any, Literal, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
import os

from src.agents.state import AgentState, FarmerInput, ExtractionModel, ValidationResult, AgriAdvice
from src.agents.prompts import (
    create_extraction_chain, 
    create_validation_chain, 
    create_advice_chain,
    EXTRACTION_SYSTEM_PROMPT,
    ADVICE_GENERATION_SYSTEM_PROMPT
)
from src.agents.integration import fetch_and_validate_environment_data

# Use OpenAI or Gemini depending on what's available
def get_llm(temperature=0.3):
    if os.environ.get("OPENAI_API_KEY"):
        return ChatOpenAI(model="gpt-4o-mini", temperature=temperature)
    elif os.environ.get("GEMINI_API_KEY"):
        return ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=temperature)
    return None

def validate_input_node(state: AgentState) -> AgentState:
    """Validate the farmer's input against environmental data."""
    # For now, we'll assume it's valid if we don't have a complex validation logic yet
    # or we can call create_validation_chain
    query = state.get("messages", [])[-1]["content"] if state.get("messages") else ""
    
    # Simple validation for now
    state["validation_result"] = ValidationResult(is_valid=True)
    return state

def extract_keywords_node(state: AgentState) -> AgentState:
    """Extract agricultural keywords from the query."""
    query = state.get("messages", [])[-1]["content"] if state.get("messages") else ""
    
    # In a real scenario, we'd use the extraction chain
    # For now, let's just mark it as processed
    state["processing_status"] = "processing"
    return state

def weather_analysis_node(state: AgentState) -> AgentState:
    """Evaluate weather conditions."""
    # Data is already in state if passed from frontend, otherwise fetch it
    if not state.get("weather_data") and state.get("location_coords"):
        env = fetch_and_validate_environment_data(
            state["location_coords"]["lat"], 
            state["location_coords"]["lon"]
        )
        state["weather_data"] = env["weather_data"]
    
    return state

def soil_analysis_node(state: AgentState) -> AgentState:
    """Analyze soil suitability."""
    if not state.get("soil_data") and state.get("location_coords"):
        env = fetch_and_validate_environment_data(
            state["location_coords"]["lat"], 
            state["location_coords"]["lon"]
        )
        state["soil_data"] = env["soil_data"]
    
    return state

def generate_advice_node(state: AgentState) -> AgentState:
    """Generate final agricultural advice."""
    llm = get_llm(temperature=0.2)
    if not llm:
        state["processing_errors"].append("No LLM available")
        state["processing_status"] = "failed"
        return state

    query = state.get("messages", [])[-1]["content"] if state.get("messages") else ""
    
    # Build prompt using state data
    weather = state.get("weather_data")
    soil = state.get("soil_data")
    
    prompt = f"""
    {ADVICE_GENERATION_SYSTEM_PROMPT}
    
    FARMER QUERY: {query}
    CROP: {state.get('farmer_input', {}).get('crop') if state.get('farmer_input') else 'Unknown'}
    
    ENVIRONMENTAL DATA:
    - Temperature: {weather.temperature_c if weather else 'Unknown'}C
    - Humidity: {weather.humidity if weather else 'Unknown'}%
    - Soil pH: {soil.soil_ph if soil else 'Unknown'}
    - Soil Moisture: {soil.soil_moisture if soil else 'Unknown'}%
    - Weather Alert: {weather.weather_alert if weather else 'None'}
    
    HISTORY: {state.get('messages', [])[:-1]}
    """
    
    response = llm.invoke(prompt)
    
    # Store the result
    content = response.content if hasattr(response, 'content') else str(response)
    if isinstance(content, list): # Handle case where it's a list of dicts
        content = " ".join([item.get('text', '') for item in content if isinstance(item, dict)])
    
    state["advice"] = AgriAdvice(recommendations=[content])
    state["messages"].append({"role": "assistant", "content": content})
    state["processing_status"] = "completed"
    
    return state

def build_graph():
    """Build the LangGraph for agricultural advice."""
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("validate_input", validate_input_node)
    workflow.add_node("extract_keywords", extract_keywords_node)
    workflow.add_node("weather_analysis", weather_analysis_node)
    workflow.add_node("soil_analysis", soil_analysis_node)
    workflow.add_node("generate_advice", generate_advice_node)

    # Define edges
    workflow.set_entry_point("validate_input")
    workflow.add_edge("validate_input", "extract_keywords")
    workflow.add_edge("extract_keywords", "weather_analysis")
    workflow.add_edge("weather_analysis", "soil_analysis")
    workflow.add_edge("soil_analysis", "generate_advice")
    workflow.add_edge("generate_advice", END)

    return workflow.compile()
