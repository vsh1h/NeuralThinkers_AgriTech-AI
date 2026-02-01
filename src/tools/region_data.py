# # File: src/tools/region_data.py
# import requests
# from geopy.geocoders import Nominatim

# # --- 1. Static Knowledge Base (Indian Context) ---
# # This maps states to their dominant soil and crops
# REGION_AGRI_MAP = {
#     "Maharashtra": {
#         "soil": "Black Soil",
#         "crops": ["Sugarcane", "Cotton", "Soybean", "Jowar"]
#     },
#     "Punjab": {
#         "soil": "Loamy",  # Alluvial
#         "crops": ["Wheat", "Rice", "Maize"]
#     },
#     "Uttar Pradesh": {
#         "soil": "Loamy",
#         "crops": ["Wheat", "Sugarcane", "Rice"]
#     },
#     "Karnataka": {
#         "soil": "Red soil",
#         "crops": ["Maize", "Cotton", "Ragi", "Coffee"]
#     },
#     "Tamil Nadu": {
#         "soil": "Red soil",
#         "crops": ["Rice", "Groundnut", "Cotton"]
#     },
#     "West Bengal": {
#         "soil": "Loamy",
#         "crops": ["Rice", "Jute", "Potato"]
#     },
#     "Gujarat": {
#         "soil": "Black Soil",
#         "crops": ["Cotton", "Groundnut", "Tobacco"]
#     },
#     "Rajasthan": {
#         "soil": "Sandy",
#         "crops": ["Bajra", "Wheat", "Mustard"]
#     },
#     # Fallback for unknown regions
#     "Default": {
#         "soil": "Loamy",
#         "crops": ["Rice", "Wheat"]
#     }
# }

# def get_location_details(lat, lon):
#     """
#     Reverse geocodes coordinates to find the State.
#     """
#     try:
#         # User-agent is required by Nominatim
#         geolocator = Nominatim(user_agent="agri_tech_ai_project")
#         location = geolocator.reverse((lat, lon), language='en', exactly_one=True)
#         address = location.raw.get('address', {})
#         state = address.get('state', 'Unknown')
#         return state
#     except Exception as e:
#         print(f"Geocoding Error: {e}")
#         return None

# def get_weather_context(lat, lon):
#     """
#     Fetches simple current weather (Rain/Temp) from Open-Meteo (No key required).
#     """
#     try:
#         url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
#         response = requests.get(url)
#         data = response.json()
#         return data.get('current_weather', {})
#     except:
#         return {}

# def fetch_agri_context(lat, lon):
#     """
#     The Main Brain: Combines Location + Weather to suggest Soil & Crops.
#     """
#     # 1. Get State
#     state = get_location_details(lat, lon)
    
#     # 2. Lookup Soil & Crops
#     data = REGION_AGRI_MAP.get(state, REGION_AGRI_MAP["Default"])
    
#     # 3. Refine Crop based on Weather (Simple Logic)
#     weather = get_weather_context(lat, lon)
#     temp = weather.get('temperature', 25)
#     is_raining = weather.get('weathercode', 0) in [51, 53, 55, 61, 63, 65] # Rain codes
    
#     suggested_crops = list(data['crops']) # Copy list
    
#     # Heuristic: If raining or very humid (implied), prioritize water-loving crops
#     if is_raining or "Rice" in suggested_crops:
#         # Move Rice to front if it exists
#         if "Rice" in suggested_crops:
#             suggested_crops.remove("Rice")
#             suggested_crops.insert(0, "Rice")
    
#     # Heuristic: If hot, prioritize Cotton/Millets
#     if temp > 30:
#         if "Cotton" in suggested_crops:
#             suggested_crops.remove("Cotton")
#             suggested_crops.insert(0, "Cotton")

#     return {
#         "detected_state": state,
#         "suggested_soil": data['soil'],
#         "suggested_crops": suggested_crops,
#         "weather_summary": f"{temp}C, {'Raining' if is_raining else 'Clear'}"
#     }


import requests
from geopy.geocoders import Nominatim


# ------------------------------------------------------------------
# 1. LOCATION (District + State)
# ------------------------------------------------------------------
def get_location_details(lat, lon):
    """
    Fetches dynamic location details including District and State
    using reverse geocoding.
    """
    try:
        geolocator = Nominatim(user_agent="agri_tech_dashboard_v1")
        location = geolocator.reverse((lat, lon), language="en", exactly_one=True)
        address = location.raw.get("address", {})

        district = (
            address.get("state_district")
            or address.get("county")
            or address.get("city")
            or "Unknown District"
        )

        state = address.get("state", "Unknown State")

        return {
            "district": district,
            "state": state,
            "full_name": f"{district}, {state}",
        }

    except Exception as e:
        print(f"Location Error: {e}")
        return {
            "district": "Unknown",
            "state": "Unknown",
            "full_name": "Unknown Location",
        }


# ------------------------------------------------------------------
# 2. SOIL DATA (SoilGrids API)
# ------------------------------------------------------------------
def get_soil_from_api(lat, lon):
    """
    Fetches real soil data from SoilGrids API.
    Determines soil texture + pH.
    """
    try:
        url = "https://rest.isric.org/soilgrids/v2.0/properties/query"
        params = {
            "lat": lat,
            "lon": lon,
            "property": ["clay", "sand", "silt", "phh2o"],
            "depth": "0-30cm",
            "value": "mean",
        }

        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        layers = data["properties"]["layers"]
        soil_values = {}

        for layer in layers:
            name = layer["name"]
            val = layer["depths"][0]["values"]["mean"]
            soil_values[name] = val

        clay = soil_values.get("clay", 0)
        sand = soil_values.get("sand", 0)
        silt = soil_values.get("silt", 0)
        ph = soil_values.get("phh2o", 70) / 10.0

        # Texture logic
        if clay > 350:
            soil_type = "Clay"
        elif sand > 500:
            soil_type = "Sandy"
        elif silt > 400:
            soil_type = "Silty"
        else:
            soil_type = "Loamy"

        return {
            "type": soil_type,
            "ph": round(ph, 1),
            "composition": f"Clay: {clay/10}%, Sand: {sand/10}%, Silt: {silt/10}%",
        }

    except Exception as e:
        print(f"Soil API Error: {e}")
        return {
            "type": "Loamy",
            "ph": 7.0,
            "composition": "Unavailable",
        }


# ------------------------------------------------------------------
# 3. WEATHER (Open-Meteo)
# ------------------------------------------------------------------
def get_weather_realtime(lat, lon):
    """
    Fetches current weather data.
    """
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}&current_weather=true"
        )
        response = requests.get(url, timeout=5)
        data = response.json()
        return data.get("current_weather", {})
    except:
        return {}


# ------------------------------------------------------------------
# 4. CROP SUGGESTION ENGINE
# ------------------------------------------------------------------
def suggest_crops_dynamic(soil_type, temp, is_raining):
    """
    Suggest crops based on soil + weather.
    """
    crops = []

    # Soil-based base crops
    if soil_type == "Clay":
        crops += ["Rice", "Sugarcane", "Cotton", "Soybean"]
    elif soil_type == "Sandy":
        crops += ["Bajra", "Groundnut", "Mustard", "Watermelon"]
    elif soil_type == "Loamy":
        crops += ["Wheat", "Maize", "Vegetables", "Pulses", "Cotton"]
    else:
        crops += ["Rice", "Wheat", "Jute"]

    # Weather refinements
    if is_raining:
        for crop in ["Rice", "Sugarcane"]:
            if crop in crops:
                crops.remove(crop)
                crops.insert(0, crop)

    if temp > 30 and "Cotton" in crops:
        crops.remove("Cotton")
        crops.insert(0, "Cotton")

    if temp < 20 and "Wheat" in crops:
        crops.remove("Wheat")
        crops.insert(0, "Wheat")

    return list(dict.fromkeys(crops))  # remove duplicates


# ------------------------------------------------------------------
# 5. MASTER FUNCTION (USED BY STREAMLIT)
# ------------------------------------------------------------------
def fetch_agri_context(lat, lon):
    """
    Final unified agri context provider.
    This is what your UI should consume.
    """
    location = get_location_details(lat, lon)
    soil = get_soil_from_api(lat, lon)
    weather = get_weather_realtime(lat, lon)

    temp = weather.get("temperature", 25)
    weather_code = weather.get("weathercode", 0)
    is_raining = weather_code in [51, 53, 55, 61, 63, 65, 80, 81, 82]

    crops = suggest_crops_dynamic(soil["type"], temp, is_raining)

    return {
        # LOCATION
        "state": location["state"],
        "district": location["district"],
        "location_name": location["full_name"],

        # SOIL
        "soil_type": soil["type"],
        "soil_ph": soil["ph"],
        "soil_composition": soil["composition"],

        # CROPS
        "recommended_crops": crops,

        # WEATHER
        "temperature": temp,
        "weather_summary": f"{temp}C, {'Raining' if is_raining else 'Clear'}",
    }
