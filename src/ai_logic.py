from typing import Dict, Any, List
import os
import random
import json

from src.agents.prompts import (
    generate_agricultural_advice, 
    extract_keywords_from_query_sync,
    generate_advice_with_environment,
    verify_farmer_claim
)
from src.agents.state import WeatherData, SoilData

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    try:
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
    except ImportError:
        from langchain.schema import SystemMessage, HumanMessage, AIMessage
    AI_AVAILABLE = True
except ImportError as e:
    print(f"Warning: AI dependencies missing ({e}). Using mock AI logic.")
    AI_AVAILABLE = False

def get_simulated_analysis(weather: Dict[str, Any], soil: Dict[str, Any]) -> Dict[str, Any]:
    temp = weather.get('temperature_c', 25)
    ph = soil.get('soil_ph', 7.0)
    
    if ph < 6.0:
        crops = ["Blueberries", "Potatoes", "Sweet Potatoes"]
        soil_note = "Your soil is acidic. These crops thrive in lower pH levels."
        actions = ["Apply agricultural lime to raise pH", "Monitor for nutrient deficiencies", "Add organic matter"]
    elif ph > 7.5:
        crops = ["Asparagus", "Beets", "Cabbage"]
        soil_note = "Your soil is alkaline. Selecting salt-tolerant crops is recommended."
        actions = ["Apply elemental sulfur", "Use acidifying fertilizers", "Ensure deep irrigation"]
    else:
        crops = ["Rice", "Wheat", "Maize", "Tomatoes"]
        soil_note = "Your soil pH is optimal (Neutral). Most major crops will thrive here."
        actions = ["Maintain current fertilization", "Monitor moisture during bloom", "Check for pests weekly"]

    return {
        "suggested_crops": crops,
        "soil_analysis": f"(Simulated) {soil_note}",
        "action_plan": actions
    }

def get_simulated_chat(prompt: str, context: Dict[str, Any]) -> str:
    prompt = prompt.lower()
    crop = context.get('crop_type', 'crop')
    
    if "water" in prompt or "irrigation" in prompt:
        return f"For your {crop}, I recommend checking soil moisture 2 inches deep. If it feels dry, irrigate early in the morning to reduce evaporation."
    elif "pest" in prompt or "bug" in prompt:
        return f"Common pests for {crop} can be managed using neem oil or integrated pest management. Check under the leaves for any early signs of infestation."
    elif "fertilizer" in prompt or "nutrient" in prompt:
        return f"Based on your soil, a balanced N-P-K fertilizer would work well for {crop}. Since your pH is {context.get('ph_level', 7.0)}, nutrients should be readily available."
    else:
        return f"That's a great question about {crop}. Generally, you should focus on maintaining stable soil moisture and monitoring for any localized weather alerts I've displayed on your dashboard."

def get_expert_analysis(weather_data: Dict[str, Any], soil_data: Dict[str, Any]) -> Dict[str, Any]:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip().strip('"').strip("'")
    
    if AI_AVAILABLE and api_key and "sk-" in api_key:
        try:
            llm = ChatOpenAI(temperature=0.7, model_name="gpt-4o-mini", openai_api_key=api_key)
            json_prompt = ChatPromptTemplate.from_template(
                """
                Analyze environmental data: Weather: {weather_data}, Soil: {soil_data}.
                Return JSON with keys: suggested_crops (list), soil_analysis (string), action_plan (list of 3).
                """
            )
            chain = json_prompt | llm
            result = chain.invoke({"weather_data": str(weather_data), "soil_data": str(soil_data)})
            clean_content = result.content.strip().replace("```json", "").replace("```", "")
            return json.loads(clean_content)
        except Exception as e:
            print(f"AI API failed, switching to Smart Simulator: {e}")

    return get_simulated_analysis(weather_data, soil_data)

def get_chat_response(messages: List[Dict[str, str]], context: Dict[str, Any]) -> str:
    """
    Get chat response using the advanced logic from src.agents.prompts.
    """
    api_key = os.environ.get("OPENAI_API_KEY", "").strip().strip('"').strip("'")
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    
    user_prompt = messages[-1]["content"] if messages else ""
    
    if (AI_AVAILABLE and api_key and "sk-" in api_key) or (gemini_key):
        try:
            # Extract historical context from messages
            history = ""
            if len(messages) > 1:
                # Exclude the last message (current prompt)
                history = "\n".join([f"{m['role']}: {m['content']}" for m in messages[:-1]])

            # Call the agent logic for generating advice
            advice = generate_agricultural_advice(
                farmer_query=user_prompt,
                soil_ph=context.get('ph_level', 7.0),
                soil_moisture=context.get('soil_moisture', 50.0),
                rainfall_mm=context.get('rainfall_mm', 0.0),
                temperature_c=context.get('temperature_c', 25.0),
                weather_alert=context.get('weather_alert', 'None'),
                history=history
            )
            return advice
        except Exception as e:
            print(f"Agent logic failed, switching to Smart Simulator: {e}")

    return get_simulated_chat(user_prompt, context)

