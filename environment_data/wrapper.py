"""
Wrapper Module - Main Entry Point

This module provides the main public function `get_environmental_context()`
which orchestrates all environmental data fetching and normalization.
"""

from typing import Dict, Any

from .gps import get_gps_location
from .weather import fetch_weather_data, process_weather_data
from .soil import fetch_soil_data, process_soil_data
from .normalize import normalize_environmental_data


def get_environmental_context() -> Dict[str, Any]:
    """
    Main function to get complete environmental context for AI agents.
    
    This function orchestrates the entire data fetching process:
    1. Gets GPS location from browser
    2. Fetches weather data from OpenWeatherMap
    3. Fetches soil data from Ambee
    4. Normalizes everything into a single structured dictionary
    
    Returns:
        Dict: Complete environmental context with structure:
            {
                "location": {
                    "latitude": float,
                    "longitude": float
                },
                "weather": {
                    "temperature_c": float,
                    "humidity": int,
                    "rainfall_mm": float | None,
                    "weather_alert": str | None
                },
                "soil": {
                    "soil_type": str | None,
                    "soil_ph": float | None,
                    "soil_moisture": float | None
                },
                "timestamp": str (ISO format)
            }
    
    Example:
        >>> context = get_environmental_context()
        >>> print(context["weather"]["temperature_c"])
        25.5
        >>> print(context["soil"]["soil_type"])
        "Clay Loam"
    """
    print("Starting environmental data collection...")
    
    # Step 1: Get GPS Location
    print("Step 1/3: Getting GPS location...")
    location = get_gps_location()
    
    # Initialize data containers
    weather_data = None
    soil_data = None
    
    # Step 2 & 3: Fetch weather and soil data (if location available)
    if location:
        print("Step 2/3: Fetching weather data...")
        raw_weather = fetch_weather_data(
            location["latitude"], 
            location["longitude"]
        )
        weather_data = process_weather_data(raw_weather) if raw_weather else None
        
        print("Step 3/3: Fetching soil data...")
        raw_soil = fetch_soil_data(
            location["latitude"], 
            location["longitude"]
        )
        soil_data = process_soil_data(raw_soil) if raw_soil else None
    else:
        print("Warning: Skipping weather and soil data (no GPS location)")
    
    # Step 4: Normalize all data into unified structure
    print("Step 4/4: Normalizing data...")
    result = normalize_environmental_data(location, weather_data, soil_data)
    
    print("Environmental data collection complete!")
    return result

