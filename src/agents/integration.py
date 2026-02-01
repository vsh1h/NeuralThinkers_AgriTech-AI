"""
Integration Layer: Prompts and Environment Tools integration.

This module bridges Pydantic data models with environmental data fetching.
Ensures type safety and data contract compliance.
"""

from typing import Optional
from environment_data.wrapper import get_environmental_context
from src.agents.state import WeatherData, SoilData


def fetch_and_validate_environment_data(latitude: float, longitude: float) -> dict:
    """
    This function:
    1. Calls environmental context fetching
    2. Extracts weather and soil data
    3. Validates against Pydantic models (WeatherData, SoilData)
    4. Returns typed data ready for processing chains
    
    Args:
        latitude: Location latitude
        longitude: Location longitude
        
    Returns:
        dict with keys:
            - weather_data: WeatherData model instance
            - soil_data: SoilData model instance
            - raw_response: Original response
    """
    try:
        # Get environmental context
        raw_env_data = get_environmental_context()
        
        # Extract weather data and validate against WeatherData model
        weather_dict = raw_env_data.get("weather", {})
        weather_data = WeatherData(
            temperature_c=weather_dict.get("temperature_c"),
            humidity=weather_dict.get("humidity", 0),
            rainfall_mm=weather_dict.get("rainfall_mm"),
            weather_alert=weather_dict.get("weather_alert")
        )
        
        # Extract soil data and validate against SoilData model
        soil_dict = raw_env_data.get("soil", {})
        soil_data = SoilData(
            soil_type=soil_dict.get("soil_type"),
            soil_ph=soil_dict.get("soil_ph"),
            soil_moisture=soil_dict.get("soil_moisture"),
            nitrogen=None,
            phosphorus=None,
            potassium=None
        )
        
        return {
            "weather_data": weather_data,
            "soil_data": soil_data,
            "raw_response": raw_env_data
        }
        
    except Exception as e:
        print(f"Error in fetch_and_validate_environment_data: {str(e)}")
        # Return default/empty data rather than failing
        return {
            "weather_data": WeatherData(
                temperature_c=None,
                humidity=0,
                rainfall_mm=None,
                weather_alert=None
            ),
            "soil_data": SoilData(
                soil_type=None,
                soil_ph=None,
                soil_moisture=None
            ),
            "raw_response": None
        }


def format_environment_for_prompt(weather_data: WeatherData, soil_data: SoilData) -> dict:
    """
    Format data into variables for prompt templates.
    
    This function converts Pydantic models into the exact variable names
    expected by prompt templates.
    
    Args:
        weather_data: WeatherData model
        soil_data: SoilData model
        
    Returns:
        dict with keys matching prompt template variables:
            - temperature_c
            - humidity
            - rainfall_mm
            - weather_alert
            - soil_ph
            - soil_moisture
            - soil_type
    """
    return {
        # Weather variables
        "temperature_c": weather_data.temperature_c or "Unknown",
        "humidity": weather_data.humidity or "Unknown",
        "rainfall_mm": weather_data.rainfall_mm or 0,
        "weather_alert": weather_data.weather_alert or "None",
        
        # Soil variables
        "soil_ph": soil_data.soil_ph or "Unknown",
        "soil_moisture": soil_data.soil_moisture or "Unknown",
        "soil_type": soil_data.soil_type or "Unknown",
    }
