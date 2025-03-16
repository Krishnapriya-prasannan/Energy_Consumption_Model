from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import requests
import os
from datetime import datetime
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Location, WeatherData

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

# Save location to the database
def save_location(db: Session, location_name: str):
    location = db.query(Location).filter(Location.location_name == location_name).first()
    if not location:
        location = Location(location_name=location_name)
        db.add(location)
        db.commit()
        db.refresh(location)
    return location

# Save weather data to the database
def save_weather_data(db: Session, weather_data: dict, location_name: str):
    location = save_location(db, location_name)

    weather_entry = WeatherData(
        location_id=location.id,
        temperature=weather_data['main']['temp'],
        humidity=weather_data['main']['humidity'],
        wind_speed=weather_data['wind']['speed'],
        visibility=weather_data['visibility'],
        pressure=weather_data['main']['pressure'],
        cloud_cover=weather_data['clouds']['all'],
        wind_bearing=weather_data['wind'].get('deg', 0),
        precip_intensity=weather_data.get('rain', {}).get('1h', 0),
        precip_probability=weather_data.get('pop', 0),
        month=datetime.now().month,
        day=datetime.now().day,
        hour=datetime.now().hour,
        weekday=datetime.now().weekday()
    )

    db.add(weather_entry)
    db.commit()
    db.refresh(weather_entry)
    return weather_entry

# Fetch current weather
@router.get("/current/")
def get_current_weather(location: str, db: Session = Depends(get_db)):
    """Fetch current weather data for a given location."""
    api_url = f"{BASE_URL}/weather?q={location}&appid={OPENWEATHER_API_KEY}&units=metric"
    weather_data = fetch_weather_data(api_url)
    save_weather_data(db, weather_data, location)  # Save to database
    return weather_data

# Fetch past 5 days weather data (OpenWeather only allows 5 days history)
@router.get("/past5days")
def get_past_weather(location: str, db: Session = Depends(get_db)):
    """Fetch past 5 days weather data for a given location."""
    lat, lon = get_coordinates(location)
    api_url = f"{BASE_URL}/onecall/timemachine?lat={lat}&lon={lon}&dt=1704067200&appid={OPENWEATHER_API_KEY}&units=metric"
    weather_data = fetch_weather_data(api_url)
    save_weather_data(db, weather_data, location)  # Save to database
    return weather_data

# Fetch historical weather data (One Call API)
@router.get("/historical")
def get_historical_weather(request: WeatherRequest, db: Session = Depends(get_db)):
    """Fetch historical weather data for a given location and date range."""
    lat, lon = get_coordinates(request.location)

    # Convert start_date & end_date to timestamps
    start_timestamp = int(datetime.strptime(request.start_date, "%Y-%m-%d").timestamp())
    end_timestamp = int(datetime.strptime(request.end_date, "%Y-%m-%d").timestamp())

    api_url = f"{BASE_URL}/onecall/timemachine?lat={lat}&lon={lon}&dt={start_timestamp}&appid={OPENWEATHER_API_KEY}&units=metric"
    weather_data = fetch_weather_data(api_url)
    save_weather_data(db, weather_data, request.location)  # Save to database
    return weather_data

# Fetch weather forecast (up to 7 days)
@router.get("/forecast/")
def get_weather_forecast(location: str, days: int = 7, db: Session = Depends(get_db)):
    """Fetch weather forecast for up to 7 days for a given location."""
    if not (1 <= days <= 7):
        raise HTTPException(status_code=400, detail="days must be between 1 and 7 (OpenWeather limit)")

    api_url = f"{BASE_URL}/forecast?q={location}&cnt={days}&appid={OPENWEATHER_API_KEY}&units=metric"
    weather_data = fetch_weather_data(api_url)
    save_weather_data(db, weather_data, location)  # Save to database
    return weather_data
