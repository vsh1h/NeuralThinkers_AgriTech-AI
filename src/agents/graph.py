from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from datetime import datetime

from src.agents.state import (
    AgentState,
    FarmerInput,
    ExtractedKeywords,
    ValidationResult,
    WeatherData,
    SoilData,
    AgriAdvice,
)

from src.tools.weather_api import get_weather_data
from src.tools.soil_service import get_soil_data
from src.database.memory import get_memory
from src.agents.prompts import SYSTEM_PROMPT


llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.3
)

# -------------------- Nodes --------------------

def validate_input_node(state: AgentState) -> AgentState:
    try:
        FarmerInput(**state["farmer_input"].dict())
        state["validation_result"] = ValidationResult(is_valid=True)
    except Exception as e:
        state["validation_result"] = ValidationResult(
            is_valid=False,
            error_message=str(e)
        )
        state["processing_status"] = "failed"
    return state


def keyword_extraction_node(state: AgentState) -> AgentState:
    farmer_input = state["farmer_input"]

    prompt = f"""
    Extract pests, symptoms, and urgency from the following farmer report.

    Crop: {farmer_input.crop}
    Action/Issue: {farmer_input.reported_action}

    Return JSON with:
    - pests (list)
    - symptoms (list)
    - urgency (low/medium/high/critical)
    """

    response = llm.invoke(prompt)
    extracted = ExtractedKeywords.model_validate_json(response.content)

    state["extracted_keywords"] = extracted
    return state


def weather_node(state: AgentState) -> AgentState:
    coords = state.get("location_coords")

    weather = get_weather_data(coords)
    state["weather_data"] = WeatherData(**weather)
    return state


def soil_node(state: AgentState) -> AgentState:
    farmer_input = state["farmer_input"]

    soil = get_soil_data(
        location=farmer_input.location,
        soil_type=farmer_input.soil_type
    )
    state["soil_data"] = SoilData(**soil)
    return state


def advice_node(state: AgentState) -> AgentState:
    farmer_input = state["farmer_input"]
    weather = state["weather_data"]
    soil = state["soil_data"]
    keywords = state["extracted_keywords"]

    prompt = f"""
    {SYSTEM_PROMPT}

    Farmer Context:
    Crop: {farmer_input.crop}
    Soil Type: {farmer_input.soil_type}
    Location: {farmer_input.location}

    Weather:
    Temperature: {weather.temperature_c}°C
    Humidity: {weather.humidity}%
    Alert: {weather.weather_alert}

    Soil Data:
    pH: {soil.soil_ph}
    Moisture: {soil.soil_moisture}

    Detected Issues:
    Pests: {keywords.pests}
    Symptoms: {keywords.symptoms}
    Urgency: {keywords.urgency}

    Task:
    Provide actionable, practical agricultural advice.
    """

    response = llm.invoke(prompt)

    state["advice"] = AgriAdvice(
        recommendations=[response.content]
    )
    state["processing_status"] = "completed"
    state["timestamp"] = datetime.utcnow().isoformat()

    return state


# -------------------- Graph Builder --------------------

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("validate_input", validate_input_node)
    graph.add_node("extract_keywords", keyword_extraction_node)
    graph.add_node("weather_analysis", weather_node)
    graph.add_node("soil_analysis", soil_node)
    graph.add_node("generate_advice", advice_node)

    graph.set_entry_point("validate_input")

    graph.add_edge("validate_input", "extract_keywords")
    graph.add_edge("extract_keywords", "weather_analysis")
    graph.add_edge("weather_analysis", "soil_analysis")
    graph.add_edge("soil_analysis", "generate_advice")
    graph.add_edge("generate_advice", END)

    return graph.compile(
        checkpointer=get_memory()
    )