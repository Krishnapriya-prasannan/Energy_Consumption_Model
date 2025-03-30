import os
import json
import subprocess
import mysql.connector
import requests
import csv
from datetime import datetime,timedelta
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, validator
from typing import Dict, List, Optional
from fastapi.middleware.cors import CORSMiddleware
import random
import pickle
import pandas as pd
import shap
import numpy as np
from collections import defaultdict
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import openai  
import google.generativeai as genai


app = FastAPI(title="Energy Consumption Prediction API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from any frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()
KSEB_API_URL = os.getenv("KSEB_API_URL")
GENAI_API_KEY = os.getenv("GENAI_API_KEY")

# Database connection function
def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        buffered=True
    )
with open("../lightgbm_model10.pkl", "rb") as model_file:
    model = pickle.load(model_file)

class Appliance(BaseModel):
    power: float
    count: int
    usageTime: str  # Kept as string but converted later
    days: List[str]
    times: Dict[str, List[str]]

    @validator("power", pre=True)
    def convert_power(cls, v):
        if isinstance(v, str):
            return float(v)  # Convert string to float
        return v

    @validator("count", pre=True)
    def convert_count(cls, v):
        if isinstance(v, str):
            return int(v)  # Convert string to int
        return v

class EnergyRequest(BaseModel):
    appliances: Dict[str, Appliance]
    location: str
    consumerNo: Optional[str] = None
    phase: Optional[str] = None
    selectedDates: Optional[List[str]] = None

    @validator("appliances", pre=True)
    def fix_appliance_usage_key(cls, v):
        # Ensure 'usage' key is renamed to 'usageTime' dynamically
        for appliance in v.values():
            if "usage" in appliance:
                appliance["usageTime"] = appliance.pop("usage")
        return v
    
# Function to fetch past consumption data from KSEB API
def fetch_past_consumption(consumer_id: str):
    try:
        print(f"\nFetching past consumption data for consumer_id: {consumer_id}") 
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Connection": "keep-alive"
        }
        data = {"optionVal": consumer_id}
        
        response = requests.post(KSEB_API_URL, headers=headers, data=data)
        response.raise_for_status()  # Raise error if request fails

        consumption_data = response.json()
        print("Consumption Data Fetched:\n", consumption_data)  # Display contents
        return consumption_data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching consumption data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching consumption data: {str(e)}")


from datetime import datetime

def format_consumption_data(consumption_data):
    """
    Formats consumption data from raw list to a dictionary with only the first six entries.
    The year is removed, keeping only the month as the key.
    
    :param consumption_data: List of dicts containing 'billmonth' and 'totalConsumption'.
    :return: Dictionary with formatted month as keys and consumption as values (only first six).
    """
    formatted_data = {}

    for entry in consumption_data[:6]:  # Take only the first six entries
        bill_month = entry["billmonth"]
        formatted_month = datetime.strptime(bill_month, "%Y%m").strftime("%B")  # Convert to 'Month' format
        total_consumption = entry["totalConsumption"]

        formatted_data[formatted_month] = total_consumption  # Store in dictionary

    # ✅ Print output before returning
    print("\n=== Formatted Consumption Data (First 6 Entries, No Year) ===")
    for month, consumption in formatted_data.items():
        print(f"{month}: {consumption} units")

    return formatted_data  # Return dictionary for easy use
# Fetch and store weather data
def fetch_and_store_weather_data(location: str, location_id: int, db):
    try:
        match = location.strip().split(", ")
        if len(match) != 2:
            raise ValueError("Invalid location format")
        
        lat, lon = match[0].split(":")[1], match[1].split(":")[1]
        response = requests.get("http://api.openweathermap.org/data/2.5/weather", params={
            "lat": lat.strip(),
            "lon": lon.strip(),
            "appid": os.getenv("OPENWEATHER_API_KEY"),
            "units": "metric"
        })
        weather_data = response.json()
        print("Fetched Weather Data:", weather_data)  # Display the fetched data

        # Extract relevant weather details
        temperature = weather_data.get("main", {}).get("temp")
        humidity = weather_data.get("main", {}).get("humidity")
        wind_speed = weather_data.get("wind", {}).get("speed")
        visibility = weather_data.get("visibility")
        pressure = weather_data.get("main", {}).get("pressure")
        cloud_cover = weather_data.get("clouds", {}).get("all")
        wind_bearing = weather_data.get("wind", {}).get("deg")
        precip_intensity = weather_data.get("rain", {}).get("1h", 0)
        precip_probability = 1 if "rain" in weather_data else 0

        # Time details
        now = datetime.now()
        month, day, hour, weekday = now.month, now.day, now.hour, now.weekday()

        # Insert or update weather data in MySQL
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO weather_data (location_id, temperature, humidity, wind_speed, visibility, pressure, cloud_cover, wind_bearing, precip_intensity, precip_probability, month, day, hour, weekday)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE temperature=%s, humidity=%s, wind_speed=%s, visibility=%s, pressure=%s, cloud_cover=%s, wind_bearing=%s, precip_intensity=%s, precip_probability=%s, month=%s, day=%s, hour=%s, weekday=%s
        """, (
            location_id, temperature, humidity, wind_speed, visibility, pressure, cloud_cover, wind_bearing,
            precip_intensity, precip_probability, month, day, hour, weekday,
            temperature, humidity, wind_speed, visibility, pressure, cloud_cover, wind_bearing,
            precip_intensity, precip_probability, month, day, hour, weekday
        ))
        db.commit()
        return weather_data
    except Exception as e:
        print("Error fetching weather data:", str(e))
        return None




def fetch_historical_weather(location: str, start_date: str, end_date: str):
    try:
        # Parse location input
        match = location.strip().split(", ")
        if len(match) != 2:
            raise ValueError("Invalid location format")

        lat, lon = match[0].split(":")[1], match[1].split(":")[1]

        # Convert start_date and end_date to previous year's same month and day
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        previous_year = start_dt.year - 1  # Use previous year
        start_date_prev_year = f"{previous_year}-{start_dt.month:02d}-{start_dt.day:02d}"
        end_date_prev_year = f"{previous_year}-{end_dt.month:02d}-{end_dt.day:02d}"

        # API call to fetch historical weather data
        response = requests.get("https://archive-api.open-meteo.com/v1/archive", params={
            "latitude": lat.strip(),
            "longitude": lon.strip(),
            "start_date": start_date_prev_year,
            "end_date": end_date_prev_year,
            "hourly": "temperature_2m,relative_humidity_2m,visibility,surface_pressure,wind_speed_10m,cloud_cover,wind_direction_10m,precipitation,precipitation_probability"
        })

        # Parse JSON response
        weather_data = response.json()

        if not isinstance(weather_data, dict) or "hourly" not in weather_data:
            raise ValueError(f"Unexpected API response format: {weather_data}")

        hourly_data = weather_data["hourly"]

        if not isinstance(hourly_data, dict):
            raise ValueError(f"Unexpected format for 'hourly' data: {hourly_data}")

        # Extract hourly weather details safely
        times = hourly_data.get("time", [])
        temperatures = [temp if temp is not None else 0 for temp in hourly_data.get("temperature_2m", [])]
        humidities = [hum if hum is not None else 0 for hum in hourly_data.get("relative_humidity_2m", [])]
        visibilities = [vis if vis is not None else 0 for vis in hourly_data.get("visibility", [0] * len(times))]
        pressures = [pres if pres is not None else 0 for pres in hourly_data.get("surface_pressure", [])]
        wind_speeds = [wind if wind is not None else 0 for wind in hourly_data.get("wind_speed_10m", [])]
        cloud_covers = [cloud if cloud is not None else 0 for cloud in hourly_data.get("cloud_cover", [])]
        wind_bearings = [wind_bear if wind_bear is not None else 0 for wind_bear in hourly_data.get("wind_direction_10m", [])]
        precip_intensities = [precip if precip is not None else 0 for precip in hourly_data.get("precipitation", [])]
        precip_probabilities = [precip_prob if precip_prob is not None else 0 for precip_prob in hourly_data.get("precipitation_probability", [0] * len(times))]

        # Group data by (month, day)
        daily_data = defaultdict(lambda: {
            "temperature": [],
            "humidity": [],
            "wind_speed": [],
            "visibility": [],
            "pressure": [],
            "cloud_cover": [],
            "wind_bearing": [],
            "precip_intensity": [],
            "precip_probability": []
        })

        for i in range(len(times)):
            dt = datetime.strptime(times[i], "%Y-%m-%dT%H:%M")
            key = (dt.month, dt.day)  # Use month and day as key

            daily_data[key]["temperature"].append(temperatures[i])
            daily_data[key]["humidity"].append(humidities[i])
            daily_data[key]["wind_speed"].append(wind_speeds[i])
            daily_data[key]["visibility"].append(visibilities[i])
            daily_data[key]["pressure"].append(pressures[i])
            daily_data[key]["cloud_cover"].append(cloud_covers[i])
            daily_data[key]["wind_bearing"].append(wind_bearings[i])
            daily_data[key]["precip_intensity"].append(precip_intensities[i])
            daily_data[key]["precip_probability"].append(precip_probabilities[i])

        # Calculate daily averages
        daily_summary = []
        for (month, day), values in daily_data.items():
            daily_summary.append({
                "month": month,
                "day": day,
                "avg_temperature": sum(values["temperature"]) / len(values["temperature"]),
                "avg_humidity": sum(values["humidity"]) / len(values["humidity"]),
                "avg_wind_speed": sum(values["wind_speed"]) / len(values["wind_speed"]),
                "avg_visibility": sum(values["visibility"]) / len(values["visibility"]),
                "avg_pressure": sum(values["pressure"]) / len(values["pressure"]),
                "avg_cloud_cover": sum(values["cloud_cover"]) / len(values["cloud_cover"]),
                "avg_wind_bearing": sum(values["wind_bearing"]) / len(values["wind_bearing"]),
                "avg_precip_intensity": sum(values["precip_intensity"]) / len(values["precip_intensity"]),
                "avg_precip_probability": sum(values["precip_probability"]) / len(values["precip_probability"])
            })
        print(f"data is {daily_summary}")
        return daily_summary

    except Exception as e:
        print("Error fetching historical weather data:", str(e))
        return None
    
def get_actual_usage(appliance_name, date, energy_request):
    if not hasattr(energy_request, "appliances") or appliance_name not in energy_request.appliances:
        print(f"Appliance {appliance_name} not found in energy request.")
        return 0.0
    
    appliance = energy_request.appliances[appliance_name]
    
    if not hasattr(appliance, "days"):
        print(f"Appliance {appliance_name} does not have usage days.")
        return 0.0

    day_of_week = date.strftime("%A")  # Get day name (e.g., Monday, Tuesday)
    print(f"Checking usage for {appliance_name} on {day_of_week}")
    
    if day_of_week not in appliance.days:
        print(f"Appliance {appliance_name} not used on {day_of_week}.")
        return 0.0
    
    if hasattr(appliance, "usageTime"):
        usage_str = appliance.usageTime
        print(f"Raw usage time for {appliance_name}: {usage_str}")
        
        try:
            return float(usage_str.replace("h", "").strip())  # ✅ Convert to float safely
        except ValueError:
            print(f"Invalid usage time format: {usage_str}")  # Debugging log
            return 0.0  # Default to 0 if conversion fails

    return 0.0



class BillRequest(BaseModel):
    lat: float
    lon: float
    predicted_use: float  # Monthly consumption in kWh
    phase: str  # '1' or '3'


# 🔥 Function to determine the STATE from latitude & longitude
def get_state_from_coords(lat, lon):
    geocode_url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
    response = requests.get(geocode_url).json()
    return response.get("address", {}).get("state", "Unknown")


# 🔥 Function to Scrape KSEB Tariff
def scrape_kseb_tariff():
    # ✅ Install & manage ChromeDriver
    service = Service(ChromeDriverManager().install())
    
    # ✅ Set up WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in the background
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # ✅ Open the KSEB webpage
        url = "https://kseb.in/articledetail/eyJpdiI6Ik5kd25uUUxzYmRZN2FiQk1iRmRQOWc9PSIsInZhbHVlIjoiRkxKQjRmc09mMWl1blg3aXY2UTdIQT09IiwibWFjIjoiZGI3YzVjMjc4NWQ2ZGFhY2Y2MjQ5MmEyNThlZTc1ZDlmZGM3M2NkODkzNGQ5YmE1NjE5NDYyNmU5MDE5MmI5OCIsInRhZyI6IiJ9"
        driver.get(url)

        # ✅ Wait for the tariff table to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )

        time.sleep(5)  # ✅ Give time for JavaScript to load

        # ✅ Get the page source
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # ✅ Debug: Check if any tables exist
        tables = soup.find_all("table")
        print(f"✅ Found {len(tables)} tables on the page.")

        if not tables:
            print("❌ No tables found. The webpage structure might have changed.")
            return {}

        table = tables[0]  # Select the first table (modify if needed)

        # ✅ Extract table rows
        rows = table.find_all("tr")
        data = []

        for row in rows:
            cols = row.find_all("td")
            cols = [col.text.strip().replace("\n\t\t\t", " ") for col in cols if col.text.strip()]  # Clean data
            if cols:
                data.append(cols)

        # ✅ Extract "LT-1 Domestic" Tariff Data
        household_tariff = {}
        start_index = None

        for i, row in enumerate(data):
            if "LT- 1- Domestic" in row[0]:  # Find starting point
                start_index = i + 2  # Skip headers
            elif start_index and "LT-" in row[0]:  # Stop at next category
                break
            elif start_index:
                household_tariff[row[0]] = row[1:]

        # ✅ Debugging Output
        print("\n🔹 KSEB Household Tariff Rates 🔹")
        for category, rates in household_tariff.items():
            print(f"{category}: {rates}")

        # ✅ Save data as JSON
        with open("kseb_household_tariff.json", "w") as f:
            json.dump(household_tariff, f, indent=4)

        return household_tariff

    finally:
        driver.quit()  # ✅ Close browser


def calculate_bill(predicted_use, phase):
    """
    Calculate the electricity bill using KSEB's tariff structure for a bi-monthly cycle.
    
    Args:
        predicted_use (int): Units consumed.
        phase (str): "1" for single-phase, "3" for three-phase.
    
    Returns:
        float: Total bill amount rounded to 2 decimal places.
    """
    if phase=='1-Phase':
        phase = "1"
    else:
        phase= "3"
    print(f"Calculating bill for Usage: {predicted_use} kWh, Phase: {phase}, Cycle: Bi-monthly")

    energy_charge_slabs = [
    (100, 3.35),   # First 100 units → ₹3.35/unit
    (100, 4.25),   # Next 100 units (101-200) → ₹4.25/unit
    (100, 5.35),   # Next 100 units (201-300) → ₹5.35/unit
    (100, 7.20),   # Next 100 units (301-400) → ₹7.20/unit
    (100, 8.50),   # Next 100 units (401-500) → ₹8.50/unit
    (500, 8.25),   # For 501-1000 units → ₹8.25/unit
        (float("inf"), 9.20)  # Above 1000 units → ₹9.20/unit
    ]

    # Compute Energy Charge
    remaining_units = predicted_use
    energy_cost = 0
    for slab_limit, rate in energy_charge_slabs:
        if remaining_units > 0:
            units_in_this_slab = min(remaining_units, slab_limit)
            energy_cost += units_in_this_slab * rate
            remaining_units -= units_in_this_slab
        else:
            break

    # Round Energy Cost
    energy_cost = round(energy_cost, 2)
    
    # Electricity Duty (10% of EC)
    duty = round(energy_cost * 0.10, 2)

    # Bi-monthly Fuel Surcharge
    fuel_surcharge = 6.56  

    # Fixed Charges (Bi-monthly cycle)
    fixed_charges = {"1": 90, "3": 240}
    fixed_charge = fixed_charges[phase]

    # Meter Rent (Bi-monthly cycle)
    meter_rent = {"1": 12, "3": 30}
    meter_rent_value = meter_rent[phase]

    # Subsidy (varies for phase)
    fixed_charge_subsidy = -40 if phase == "1" else 0
    ec_subsidy = -29 if (phase == "1" and predicted_use <= 50) else 0

    # Final Bill Calculation
    total_bill = (
        energy_cost + duty + fuel_surcharge + fixed_charge + meter_rent_value
        + fixed_charge_subsidy + ec_subsidy
    )
    print(f"Total Bill: {total_bill} ₹")  # Debugging log
    return round(total_bill, 2)



def predict_energy_usage(csv_file_path, appliance_power_ratings, min_use, energy_request):
    try:
        # Load simulated data from CSV
        data = pd.read_csv(csv_file_path)

        # Ensure feature columns match model expectations
        feature_columns = getattr(model, "feature_names_in_", data.columns)  
        data = data[feature_columns]
        print(f"Feature columns: {feature_columns}")  # Debugging log

        # Predict energy consumption (normalized values)
        predictions = model.predict(data)
        print(f"Predictions: {predictions}")  # Debugging log

        # Convert selected dates to datetime format
        selected_dates = sorted([datetime.strptime(date, "%a %b %d %Y") for date in energy_request.selectedDates])
        print(f"Selected Dates: {selected_dates}")  # Debugging log

        # Compute daily max_use dynamically
        max_use_per_day = []
        for date in selected_dates:
            max_use = sum(
                ((appliance["power"] * appliance["count"]) / 1000) * 
                get_actual_usage(appliance_name, date, energy_request) 
                for appliance_name, appliance in appliance_power_ratings.items()
            )
            max_use_per_day.append(max_use)

        max_use_per_day = np.array(max_use_per_day)
        print(f"Max use per day: {max_use_per_day}")

        # Handle division by zero by setting to a small value
        max_use_per_day[max_use_per_day == 0] = 0  

        # Denormalize predictions using daily max_use
        denormalized_predictions = predictions * (max_use_per_day - min_use) + min_use

        # Create DataFrame
        prediction_df = pd.DataFrame({
            "date": selected_dates,
            "predicted_use": denormalized_predictions
        })

        # Convert 'date' to datetime format before merging
        prediction_df["date"] = pd.to_datetime(prediction_df["date"])

        # Ensure a complete date range, filling missing dates with zero consumption
        full_date_range = pd.date_range(start=min(selected_dates), end=max(selected_dates))
        full_prediction_df = pd.DataFrame({"date": full_date_range})

        # Merge with predictions, filling missing values with 0
        full_prediction_df = full_prediction_df.merge(prediction_df, on="date", how="left").fillna(0)

        # Convert date column to string for output
        full_prediction_df["date"] = full_prediction_df["date"].dt.strftime("%Y-%m-%d")

        # Group by month & sum predicted use
        full_prediction_df["year_month"] = pd.to_datetime(full_prediction_df["date"]).dt.to_period("M")
        monthly_totals = full_prediction_df.groupby("year_month")["predicted_use"].sum().reset_index()

        # Convert year_month to string
        monthly_totals["year_month"] = monthly_totals["year_month"].astype(str)

        # Sum total energy usage after filling missing dates
        total_energy_usage = round(full_prediction_df["predicted_use"].sum(), 2)
        all_dates = full_prediction_df["date"].tolist()
        
        print(f"Final Prediction Data: {full_prediction_df}")  # Debugging log
        print(f"Monthly Totals: {monthly_totals}")  # Debugging log
        print(f"All Dates: {all_dates}")  # Debugging log
        
        return {
            "totalEnergyUsage": total_energy_usage,
            "predicted_energy": full_prediction_df.to_dict(orient="records"),
            "monthly_forecast": monthly_totals.to_dict(orient="records"),
            "all_dates": all_dates  # ✅ Includes all dates
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@app.post("/predict-energy")
async def predict_energy(request: EnergyRequest, db=Depends(get_db)):
    cursor = db.cursor()

    # Validate input data
    if not request.selectedDates or len(request.selectedDates) < 2:
        raise HTTPException(status_code=400, detail="Please provide at least two dates for weather data")

    appliances = request.appliances
    location = request.location
    past_consumption_data = None

    if request.consumerNo:
        try:
            past_consumption_data = fetch_past_consumption(request.consumerNo)
            past_consumption_data = format_consumption_data(past_consumption_data)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching past consumption: {str(e)}")

    # Check if location exists, else insert it
    try:
        cursor.execute("SELECT id FROM locations WHERE location_name = %s", (location,))
        location_row = cursor.fetchone()
        if location_row:
            location_id = location_row[0]
        else:
            cursor.execute("INSERT INTO locations (location_name) VALUES (%s)", (location,))
            db.commit()
            location_id = cursor.lastrowid  
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # Convert date format to YYYY-MM-DD
    try:
        formatted_dates = sorted([datetime.strptime(date, "%a %b %d %Y").strftime("%Y-%m-%d") for date in request.selectedDates])
        start_date, end_date = formatted_dates[0], formatted_dates[-1]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Expected 'Tue Mar 11 2025' format")

    # Fetch and store historical weather data
    try:
        weather_data = fetch_historical_weather(location, start_date, end_date)
        if not weather_data:
            raise HTTPException(status_code=400, detail="Could not fetch weather data")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather data fetch error: {str(e)}")
    
    # Insert appliances into the database
    try:
        for appliance_name, appliance in appliances.items():
            usage_hours = float(appliance.usageTime.replace("h", "").strip()) if hasattr(appliance, "usageTime") else 0.0
            days_data = json.dumps(appliance.days) if hasattr(appliance, "days") else "[]"
            times_data = json.dumps(appliance.times) if hasattr(appliance, "times") else "{}"

            cursor.execute("""
                INSERT INTO appliances (name, power_rating, count, usage_hours, usage_days, time_of_usage)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                appliance_name,
                appliance.power if hasattr(appliance, "power") else 0,  
                appliance.count if hasattr(appliance, "count") else 1,  
                usage_hours,
                days_data,
                times_data
            ))

        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error inserting appliances: {str(e)}")

    # Simulate data and save to CSV
    try:
        simulated_data = generate_simulated_data(appliances, weather_data, formatted_dates)
        if simulated_data.empty:
            raise HTTPException(status_code=500, detail="Simulated data is empty")
        csv_file_path = save_data_to_csv(simulated_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")

    # Run prediction using the trained LightGBM model
    try:
        min_use=0
        appliance_power_ratings = {
    str(name): {"power": appliance.power, "count": appliance.count}  
    for name, appliance in appliances.items()
}

        print(f"CSV Path: {csv_file_path}")
        print(f"Appliance Power Ratings: {appliance_power_ratings}")  # Ensure keys are strings
        print(f"Type of appliance_power_ratings: {type(appliance_power_ratings)}")


        prediction_result = predict_energy_usage(csv_file_path, appliance_power_ratings, min_use, request)
        print(f"Raw prediction result{prediction_result}")

        if not prediction_result or not isinstance(prediction_result, dict):
            raise HTTPException(status_code=500, detail="Invalid prediction response format")

        monthly_forecast = prediction_result.get("monthly_forecast", [])
    
    # Ensure it's a list
        if isinstance(monthly_forecast, dict):  
            monthly_forecast = [monthly_forecast] 

        consumption_data = [
    {"month": str(d["year_month"]), "units": d["predicted_use"]}
    for d in monthly_forecast
]


    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

    print(f"consumption data :{consumption_data}")
    """try:
        tariff_data=scrape_kseb_tariff()
        print(f"Tariff Data: {tariff_data}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tariff data: {str(e)}")"""

    return {
        "prediction": prediction_result,
        "bill": calculate_bill(sum(entry["predicted_use"] for entry in prediction_result["predicted_energy"]), request.phase),
        "billAmount": calculate_bill_amount(
            [entry["predicted_use"] for entry in prediction_result["predicted_energy"]], 
            request.phase
),
        "recommendations": get_recommendations(
    prediction_result["predicted_energy"],
    past_consumption_data,
    request.appliances
    ),
        "pastConsumption": past_consumption_data,  # Include past consumption in response
        "weatherData": weather_data,  # Include weather data
        "consumptionData": consumption_data  # Include consumption data for graph
    }


@app.post("/submit")
async def submit_data(request: EnergyRequest, db=Depends(get_db)):
    try:
        print("Received data:", request.dict())  # Debug log
        result = await predict_energy(request, db)  # Direct function call
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/")
def home():
    return {"message": "Welcome to Energy Prediction API"}


appliance_mapping = {
    "Dishwasher": "Dishwasher",
    "Air Conditioner": "AirConditioner",
    "Heater": "Heater",
    "Computer Devices": "ComputerDevices",
    "Refrigerator": "Refrigerator",
    "Washing Machine": "WashingMachine",
    "Fans": "Fans",
    "Chimney": "Chimney",
    "Food Processor": "FoodProcessor",
    "Induction Cooktop": "InductionCooktop",
    "Lights": "Lights",
    "Water Pump": "WaterPump",
    "Microwave": "Microwave",
    "TV": "TV"
}

# Default weather values (used if API fails)
default_weather = {
    "temperature": 25,
    "humidity": 50,
    "windSpeed": 5,
    "visibility": 0,
    "pressure": 1013,
    "cloudCover": 10,
    "windBearing": 180,
    "precipIntensity": 0,
    "precipProbability": 0
}

def is_valid_usage_time(hour, time_ranges):
    """Maps named times (Morning, Noon, etc.) to specific hour ranges."""
    hour_mapping = {
        "Morning": range(6, 12),
        "Noon": range(12, 14),
        "Evening": range(17, 20),
        "Night": range(20, 24)
    }
    return any(hour in hour_mapping.get(t, []) for t in time_ranges)

def generate_simulated_data(appliances, weather_records, selected_dates):
    """Generates simulated energy consumption data only for selected dates based on user appliances and historical weather data."""
    
    simulated_data = []
    
    if not selected_dates:
        return pd.DataFrame()  # Return empty DataFrame if no dates selected
    
    selected_dates = sorted(selected_dates)  # Ensure dates are in order
    
    # Convert weather_records into a dictionary {(month, day): weather_data}
    weather_dict = {(record["month"], record["day"]): record for record in weather_records}

    for date_str in selected_dates:
        current_date = datetime.strptime(date_str, "%Y-%m-%d")
        month, day, hour, weekday = current_date.month, current_date.day, current_date.hour, current_date.weekday()
        
        # Get historical weather data for the current date, fallback to default if not found
        weather_data = weather_dict.get((month, day), default_weather)

        # Initialize row with 0s for all appliances
        row = {name: 0.0 for name in appliance_mapping.values()}
        
        # Process each appliance
        for frontend_name, appliance_data in appliances.items():
            dataset_name = appliance_mapping.get(frontend_name.strip())

            # Convert Pydantic model to dictionary if needed
            if hasattr(appliance_data, "model_dump"):  
                appliance_data = appliance_data.model_dump()  # Pydantic v2
            elif hasattr(appliance_data, "dict"):  
                appliance_data = appliance_data.dict()  # Pydantic v1

            if dataset_name and isinstance(appliance_data, dict):
                try:
                    usage_hours = float(appliance_data.get("usageTime", "0h").replace("h", "").strip())
                except ValueError:
                    usage_hours = 0.0  # Handle invalid usageTime

                power_rating = float(appliance_data.get("power", 0))  # Ensure power is float
                quantity = int(appliance_data.get("count", 1))  # Get number of appliances

                # Compute power usage (adapting from the previous method)
                base_usage = usage_hours * quantity * power_rating
                
                # Adjust based on weather conditions
                temperature = weather_data.get("avg_temperature", default_weather["temperature"])
                humidity = weather_data.get("avg_humidity", default_weather["humidity"])
                cloud_cover = weather_data.get("avg_cloud_cover", default_weather["cloudCover"])
                
                # Appliance-specific weather-based adjustments
                if "AirConditioner" in dataset_name:
                    if temperature > 30:
                        base_usage *= 1.5  # Increase usage during hot weather
                    elif temperature < 15:
                        base_usage *= 0.8  # Decrease usage in cold weather
                elif "Fan" in dataset_name and temperature > 25:
                    base_usage *= 1.2
                elif "Heater" in dataset_name and temperature < 10:
                    base_usage *= 1.5
                elif "Lights" in dataset_name and cloud_cover > 70:
                    base_usage *= 1.1  # Increase light usage on cloudy days
                
                row[dataset_name] = round(base_usage, 2)  # Store rounded values

        # Add historical weather data to the row
        row.update({
            "temperature": weather_data.get("avg_temperature", default_weather["temperature"]),
            "humidity": weather_data.get("avg_humidity", default_weather["humidity"]),
            "visibility": weather_data.get("avg_visibility", default_weather["visibility"]),
            "pressure": weather_data.get("avg_pressure", default_weather["pressure"]),
            "windSpeed": weather_data.get("avg_wind_speed", default_weather["windSpeed"]),
            "cloudCover": weather_data.get("avg_cloud_cover", default_weather["cloudCover"]),
            "windBearing": weather_data.get("avg_wind_bearing", default_weather["windBearing"]),
            "precipIntensity": weather_data.get("avg_precip_intensity", default_weather["precipIntensity"]),
            "precipProbability": weather_data.get("avg_precip_probability", default_weather["precipProbability"]),
            "month": month,
            "day": day,
            "hour": hour,
            "weekday": weekday
        })

        simulated_data.append(row)

    # Convert to DataFrame
    df = pd.DataFrame(simulated_data)

    # Convert selected_dates to datetime format and use it as the index
    df.index = pd.to_datetime(selected_dates)
    
    return df

def save_data_to_csv(data):
    """Saves the simulated data to a CSV file."""
    file_path = "simulated_data.csv"
    
    if isinstance(data, pd.DataFrame):
        data.to_csv(file_path, index=False)  # Directly save Pandas DataFrame
    elif isinstance(data, list) and data:  # Handle list of dicts
        with open(file_path, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=list(data[0].keys()))
            writer.writeheader()
            writer.writerows(data)
    else:
        raise ValueError("Invalid data format for CSV export")

    print(f"CSV saved successfully: {file_path}")  # Debugging Log
    return file_path




# Retrieve API URL from .env
API_URL = os.getenv("KSEB_BILL_URL")
def calculate_bill_amount(predictions, phase):
    if not isinstance(predictions, list):
        raise ValueError(f"Error: Expected a list but got {type(predictions)}.")

    # Convert predictions list into a DataFrame
    predicted_energy = pd.DataFrame({"predicted_use": predictions})
    
    print(f"Predicted Energy Data:\n{predicted_energy}")  # Debugging log

    # Use the current month since no date column exists
    predicted_energy["month"] = datetime.now().month  

    # Group by month to calculate total energy consumption per month
    monthly_consumption = predicted_energy.groupby("month")["predicted_use"].sum()

    bill_summary_single = {}
    bill_summary_bi = {}

    formatted_phase = str(phase).split('-')[0]  # Extract only the number

    print(f"Monthly Consumption: {monthly_consumption}")

    for month, units in monthly_consumption.items():
        payload_single = {
            "tariff_id": 1,
            "purpose_id": 15,
            "frequency": 1,  # Single-month billing
            "WNL": 1,
            "phase": formatted_phase,
            "load": max(int(units*1000), 0)  # Ensure non-negative load
        }

        payload_bi = {
            "tariff_id": 1,
            "purpose_id": 15,
            "frequency": 2,  # Bi-monthly billing
            "WNL": 1,
            "phase": formatted_phase,
            "load": max(int(units*1000), 0)
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        print(f"Converted Load for API: {max(int(units * 1000), 0)} W")

        try:
            response_single = requests.post(API_URL, headers=headers, data=payload_single)
            response_single.raise_for_status()
            data_single = response_single.json()
            print("Raw API Response:", data_single)
            if data_single.get("err_flag") == 0 and "result_data" in data_single:
                bill_summary_single[month] = data_single["result_data"]["tariff_values"].get("bill_total", {}).get("value", 0)
            else:
                print(f"API Error (Single-month) for Month {month}: {data_single}")
                bill_summary_single[month] = 0
        except requests.RequestException as e:
            print(f"Request failed for Single-month billing (Month {month}): {e}")
            bill_summary_single[month] = 0

        try:
            response_bi = requests.post(API_URL, headers=headers, data=payload_bi)
            response_bi.raise_for_status()
            data_bi = response_bi.json()
            print("Raw API Response bi:", data_bi)
            if data_bi.get("err_flag") == 0 and "result_data" in data_bi:
                bill_summary_bi[month] = data_bi["result_data"].get("bill_total", {}).get("value", 0)
            else:
                print(f"API Error (Bi-monthly) for Month {month}: {data_bi}")
                bill_summary_bi[month] = 0
        except requests.RequestException as e:
            print(f"Request failed for Bi-monthly billing (Month {month}): {e}")
            bill_summary_bi[month] = 0

    print(f"Total Bill (Single): {sum(bill_summary_single.values())}, Total Bill (Bi): {sum(bill_summary_bi.values())}")

    return sum(bill_summary_single.values()) if len(monthly_consumption) == 1 else sum(bill_summary_bi.values())

""" def get_recommendations(feature_data):
    try:
        if isinstance(feature_data, dict):
            feature_data = pd.DataFrame([feature_data])  # Convert dict to DataFrame
        print(f"Feature Data for SHAP: {feature_data}")  # Debugging log
        print(f"Feature Data Shape: {feature_data.shape}")  # Debugging log

        # Ensure feature_data contains all 27 features used in training
        if feature_data.shape[1] != 27:
            return ["Feature mismatch: Expected 27 features but got {}.".format(feature_data.shape[1])]
        # Initialize SHAP explainer
        explainer = shap.Explainer(model)

        # Generate SHAP values
        shap_values = explainer(feature_data)

        # Get feature importance
        importance = np.abs(shap_values.values).mean(axis=0)
        feature_names = feature_data.columns
        feature_importance = dict(zip(feature_names, importance))

        # Sort features by importance
        sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        print("Sorted Features:", sorted_features)  # Debugging log
        # Generate recommendations based on high-impact features
        recommendations = []
        for feature, impact in sorted_features[:3]:  # Top 3 influential features
            if "AC" in feature:
                print(f"AC usage detected in feature: {feature}")
                recommendations.append("Your AC usage is high. Reduce usage or use energy-efficient settings.")
            elif "Heater" in feature:
                print(f"Heater usage detected in feature: {feature}")
                recommendations.append("Consider using a thermostat or energy-efficient heating solutions.")
            elif "PeakHours" in feature:
                print(f"Peak hours detected in feature: {feature}")
                recommendations.append("Shift some appliance usage to non-peak hours to save on electricity bills.")
            else:
                print(f"General recommendation for feature: {feature}")
                recommendations.append(f"Optimize your usage of {feature} to lower energy consumption.")

        return recommendations

    except Exception as e:
        return [f"Error generating recommendations: {str(e)}"] """




def get_recommendations(predicted_energy, past_consumption, appliances):
    try:
        if not GENAI_API_KEY:
            return ["Error: Missing GenAI API key. Check your .env file."]

        # Configure GenAI with API key
        genai.configure(api_key=GENAI_API_KEY)

        # Select the best model dynamically
        
        # Ensure past consumption is a DataFrame
        if isinstance(past_consumption, dict):
            past_consumption = pd.DataFrame([past_consumption])
        elif not isinstance(past_consumption, pd.DataFrame):
            return ["Error: past_consumption should be a DataFrame or a dictionary."]

        print(f"Predicted Energy Usage: {predicted_energy}")
        print(f"Past Consumption Data:\n{past_consumption}")
        print(f"Appliance Details: {appliances}")

        # Convert predicted_energy list to average usage
        if isinstance(predicted_energy, list) and predicted_energy:
            predicted_energy = sum(d["predicted_use"] for d in predicted_energy) / len(predicted_energy)
        elif isinstance(predicted_energy, list) and not predicted_energy:
            return ["Error: No predicted energy data provided."]
        elif not isinstance(predicted_energy, (int, float)):
            return ["Error: predicted_energy should be a number or a list of dictionaries with 'predicted_use'."]

        # Generate structured prompt for GenAI
        prompt = f"""
        The predicted energy usage is **{predicted_energy:.2f} kWh**.
        
        **Past Energy Consumption Data:**
        ```
        {past_consumption.to_string(index=False)}
        ```

        **User's Appliances:** {", ".join(appliances)}

        **Provide recommendations including:**
        - Optimization strategies for using appliances efficiently.
        - General energy-saving tips.
        - Specific suggestions based on past consumption trends.
        """

        # Call the best available Google GenAI model
        model = genai.GenerativeModel("models/gemini-2.0-flash-001")
        response = model.generate_content(prompt)
        print(f"GenAI Response: {response}")  # Debugging log   
        return response.text.split("\n") if response.text else ["No recommendations received."]

    except Exception as e:
        return [f"Error generating recommendations: {str(e)}"]
