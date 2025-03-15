import pandas as pd
import requests
import numpy as np
from datetime import datetime, timedelta

# Fetch Weather Data Function
def get_weather_data(location):
    API_KEY = "c750e950139978d8bcc42a3ec844922f"  # Replace with your actual API key
    url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={API_KEY}&units=metric"

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return {
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "visibility": data.get("visibility", 10000),  # Default 10km
            "pressure": data["main"]["pressure"],
            "windSpeed": data["wind"]["speed"],
            "cloudCover": data["clouds"]["all"],
            "windBearing": data["wind"].get("deg", 0),
            "precipIntensity": np.random.uniform(0, 0.2),  # Simulated precipitation
            "precipProbability": np.random.uniform(0, 1)  # Simulated probability
        }
    else:
        print("Error fetching weather data")
        return None

# Simulate 3 Months of Data
def generate_simulated_data(user_input):
    location = user_input.get("location", "default_city")
    weather_data = get_weather_data(location)

    if weather_data is None:
        return None  # Stop if weather data can't be fetched

    num_days = 90  # Generate for 3 months
    start_date = datetime.today()
    data_list = []

    for i in range(num_days):
        current_date = start_date + timedelta(days=i)
        
        # Extract date details
        month = current_date.month
        day = current_date.day
        hour = np.random.randint(0, 24)  # Simulating random hour
        weekday = current_date.weekday()

        # Populate appliance usage (0 if not used)
        simulated_entry = {
            "Dishwasher": user_input.get("Dishwasher", 0),
            "AirConditioner": user_input.get("AirConditioner", 0),
            "Heater": user_input.get("Heater", 0),
            "ComputerDevices": user_input.get("ComputerDevices", 0),
            "Refrigerator": user_input.get("Refrigerator", 0),
            "WashingMachine": user_input.get("WashingMachine", 0),
            "Fans": user_input.get("Fans", 0),
            "Chimney": user_input.get("Chimney", 0),
            "FoodProcessor": user_input.get("FoodProcessor", 0),
            "InductionCooktop": user_input.get("InductionCooktop", 0),
            "Lights": user_input.get("Lights", 0),
            "WaterPump": user_input.get("WaterPump", 0),
            "Microwave": user_input.get("Microwave", 0),
            "TV": user_input.get("TV", 0),

            # Weather Data
            "temperature": weather_data["temperature"] + np.random.uniform(-2, 2),
            "humidity": weather_data["humidity"] + np.random.uniform(-5, 5),
            "visibility": weather_data["visibility"],
            "pressure": weather_data["pressure"],
            "windSpeed": weather_data["windSpeed"],
            "cloudCover": weather_data["cloudCover"],
            "windBearing": weather_data["windBearing"],
            "precipIntensity": weather_data["precipIntensity"],
            "precipProbability": weather_data["precipProbability"],

            # Date Features
            "month": month,
            "day": day,
            "hour": hour,
            "weekday": weekday
        }
        data_list.append(simulated_entry)

    df = pd.DataFrame(data_list)
    return df
