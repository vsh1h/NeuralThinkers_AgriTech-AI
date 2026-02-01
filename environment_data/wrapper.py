import random
from typing import Dict, Any

from .gps import get_gps_location
from .weather import fetch_weather_data, process_weather_data
from .soil import fetch_soil_data, process_soil_data
from .normalize import normalize_environmental_data

def get_mock_data():
    return {
        "weather": {
            "temperature_c": round(random.uniform(22.0, 32.0), 1),
            "humidity": random.randint(40, 80),
            "rainfall_mm": round(random.uniform(0.0, 15.0), 1),
            "weather_alert": random.choice(["None", "High Heat Alert", "None", "None"])
        },
        "soil": {
            "soil_type": random.choice(["Loamy", "Clay", "Sandy Loam", "Silt"]),
            "soil_ph": round(random.uniform(6.0, 7.5), 1),
            "soil_moisture": round(random.uniform(30.0, 60.0), 1)
        }
    }

def get_environmental_context() -> Dict[str, Any]:
    print("Starting environmental data collection...")
    
    location = get_gps_location()
    
    weather_data = None
    soil_data = None
    
    mock = get_mock_data()
    
    if location:
        try:
            raw_weather = fetch_weather_data(location["latitude"], location["longitude"])
            if raw_weather:
                weather_data = process_weather_data(raw_weather)
            else:
                weather_data = mock["weather"]
        except Exception as e:
            weather_data = mock["weather"]

        try:
            raw_soil = fetch_soil_data(location["latitude"], location["longitude"])
            if raw_soil:
                soil_data = process_soil_data(raw_soil)
            else:
                soil_data = mock["soil"]
        except Exception as e:
            soil_data = mock["soil"]
            
    else:
        weather_data = mock["weather"]
        soil_data = mock["soil"]
    
    result = normalize_environmental_data(location, weather_data, soil_data)
    
    print("Environmental data collection complete!")
    return result
