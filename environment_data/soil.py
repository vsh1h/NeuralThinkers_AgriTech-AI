"""
Soil API Integration Module

This module handles Ambee Soil API integration for soil data.
"""

from typing import Optional, Dict, Any
import requests

from .config import get_ambee_api_key, get_api_timeout


def fetch_soil_data(
    latitude: float, 
    longitude: float,
    timeout: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Fetch soil data from Ambee Soil API.
    
    Args:
        latitude: GPS latitude coordinate
        longitude: GPS longitude coordinate
        
    Returns:
        Optional[Dict]: Raw soil API response or None if failed
    """
    try:
        api_key = get_ambee_api_key()
        
        # Ambee Soil API endpoint
        url = "https://api.ambeedata.com/soil/latest/by-lat-lng"
        
        # Parameters for the API call
        params = {
            "lat": latitude,
            "lng": longitude
        }
        
        # Headers with API key
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
        
        # Use provided timeout or get from config
        request_timeout = timeout if timeout is not None else get_api_timeout()
        
        # Make the API request with timeout
        response = requests.get(url, params=params, headers=headers, timeout=request_timeout)
        
        # Check if request was successful
        if response.status_code == 403:
            print("Error: Invalid or expired Ambee API key")
            return None
        
        if response.status_code == 404:
            print("Error: Soil data not found for this location")
            return None
        
        response.raise_for_status()
        
        # Parse JSON response
        return response.json()
        
    except requests.exceptions.Timeout:
        print("Error: Soil API request timed out")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching soil data: {str(e)}")
        return None
    except Exception as e:
        print(f"Unexpected error in fetch_soil_data: {str(e)}")
        return None


def process_soil_data(raw_soil: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize raw Ambee Soil API response into standardized format.
    
    Args:
        raw_soil: Raw JSON response from Ambee Soil API
        
    Returns:
        Dict: Normalized soil data with keys:
            - soil_type: Type of soil (or None)
            - soil_ph: pH level (or None)
            - soil_moisture: Moisture percentage (or None)
    """
    try:
        # Ambee returns data in a "soil" key or directly at root
        soil_info = raw_soil.get("soil", raw_soil)
        
        # Extract soil type
        soil_type = soil_info.get("soilType") or soil_info.get("soil_type")
        
        # Extract soil pH (usually between 0-14)
        soil_ph = soil_info.get("ph") or soil_info.get("soilPH")
        
        # Extract soil moisture (percentage)
        soil_moisture = soil_info.get("moisture") or soil_info.get("soilMoisture")
        
        return {
            "soil_type": str(soil_type) if soil_type is not None else None,
            "soil_ph": float(soil_ph) if soil_ph is not None else None,
            "soil_moisture": float(soil_moisture) if soil_moisture is not None else None
        }
        
    except Exception as e:
        print(f"Error processing soil data: {str(e)}")
        return {
            "soil_type": None,
            "soil_ph": None,
            "soil_moisture": None
        }

