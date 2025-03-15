from fastapi import APIRouter, HTTPException
import requests
import os
from pydantic import BaseModel

router = APIRouter()

# Load the OpenWeatherMap API key from environment variables
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

if not OPENWEATHER_API_KEY:
    raise ValueError("API key is missing! Please add OPENWEATHER_API_KEY in your .env file.")

# Base URL for OpenWeatherMap API
BASE_URL = "https://api.openweathermap.org/data/2.5"

# Define request model for historical weather
class WeatherRequest(BaseModel):
    location: str
    start_date: str  # Format: YYYY-MM-DD
    end_date: str    # Format: YYYY-MM-DD

# Function to fetch weather data from API
def fetch_weather_data(api_url: str):
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=response.status_code, detail="Error fetching weather data")

# Get latitude & longitude for a location (used for historical data)
def get_coordinates(location: str):
    geocode_url = f"http://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={OPENWEATHER_API_KEY}"
    response = requests.get(geocode_url).json()
    
    if not response:
        raise HTTPException(status_code=404, detail="Location not found")

    return response[0]["lat"], response[0]["lon"]

# Fetch current weather
@router.get("/current/")
def get_current_weather(location: str):
    """Fetch current weather data for a given location."""
    api_url = f"{BASE_URL}/weather?q={location}&appid={OPENWEATHER_API_KEY}&units=metric"
    return fetch_weather_data(api_url)

# Fetch past 5 days weather data (OpenWeather only allows 5 days history)
@router.get("/past5days")
def get_past_weather(location: str):
    """Fetch past 5 days weather data for a given location."""
    lat, lon = get_coordinates(location)
    api_url = f"{BASE_URL}/onecall/timemachine?lat={lat}&lon={lon}&dt=1704067200&appid={OPENWEATHER_API_KEY}&units=metric"
    return fetch_weather_data(api_url)

# Fetch historical weather data (One Call API)
@router.get("/historical")
def get_historical_weather(request: WeatherRequest):
    """Fetch historical weather data for a given location and date range."""
    lat, lon = get_coordinates(request.location)

    # Convert start_date & end_date to timestamps
    from datetime import datetime
    start_timestamp = int(datetime.strptime(request.start_date, "%Y-%m-%d").timestamp())
    end_timestamp = int(datetime.strptime(request.end_date, "%Y-%m-%d").timestamp())

    api_url = f"{BASE_URL}/onecall/timemachine?lat={lat}&lon={lon}&dt={start_timestamp}&appid={OPENWEATHER_API_KEY}&units=metric"

    return fetch_weather_data(api_url)

# Fetch weather forecast (up to 7 days)
@router.get("/forecast/")
def get_weather_forecast(location: str, days: int = 7):
    """Fetch weather forecast for up to 7 days for a given location."""
    if not (1 <= days <= 7):
        raise HTTPException(status_code=400, detail="days must be between 1 and 7 (OpenWeather limit)")

    api_url = f"{BASE_URL}/forecast?q={location}&cnt={days}&appid={OPENWEATHER_API_KEY}&units=metric"

    return fetch_weather_data(api_url)
