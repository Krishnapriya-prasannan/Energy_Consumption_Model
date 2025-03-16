import os
import json
import subprocess
import mysql.connector
import requests
import csv
from datetime import datetime,timedelta
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List
from fastapi.middleware.cors import CORSMiddleware
import random
import pickle
import pandas as pd
import shap
import numpy
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

# Database connection function
def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        buffered=True
    )
with open("../lightgbm_model3.pkl", "rb") as model_file:
    model = pickle.load(model_file)

# Request models
class Appliance(BaseModel):
    power: float
    count: int
    usageTime: str  # Kept as string but converted later
    days: List[str]
    times: Dict[str, List[str]]

class EnergyRequest(BaseModel):
    appliances: Dict[str, Appliance]
    location: str

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
def predict_energy_usage(csv_file_path):
    try:
        # Load simulated data from CSV
        data = pd.read_csv(csv_file_path)

        # Ensure feature columns match model expectations
        feature_columns = model.feature_name_
        data = data[feature_columns]

        # Predict energy consumption
        predictions = model.predict(data)

        # Generate future dates assuming each row represents a day
        start_date = datetime.today()
        future_dates = [start_date + timedelta(days=i) for i in range(len(predictions))]

        # Create DataFrame with required format
        predicted_energy = pd.DataFrame({
            "date": future_dates,
            "predicted_use": predictions
        })

        # Sum total energy usage over the 90 days
        total_energy_usage = round(sum(predictions), 2)

        return {
            "totalEnergyUsage": total_energy_usage,
            "predicted_energy": predicted_energy.to_dict(orient="records")  # Convert to list of dicts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")
@app.post("/predict-energy")
async def predict_energy(request: EnergyRequest, db=Depends(get_db)):
    appliances = request.appliances
    location = request.location
    cursor = db.cursor()

    # Check if the location exists in the database
    cursor.execute("SELECT id FROM locations WHERE location_name = %s", (location,))
    location_row = cursor.fetchone()

    if location_row:
        location_id = location_row[0]
    else:
        cursor.execute("INSERT INTO locations (location_name) VALUES (%s)", (location,))
        location_id = cursor.lastrowid
        db.commit()

    # Fetch and store weather data
    weather_data = fetch_and_store_weather_data(location, location_id, db)
    if not weather_data:
        raise HTTPException(status_code=400, detail="Could not fetch weather data")

    # Insert appliances into DB
    for appliance_name, appliance in appliances.items():
        try:
            usage_hours = float(appliance.usageTime.replace("h", "").strip())  # Convert "3h" -> 3.0

            cursor.execute("""
                INSERT INTO appliances (name, power_rating, count, usage_hours, usage_days, time_of_usage)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                appliance_name,
                appliance.power,
                appliance.count,
                usage_hours,
                json.dumps(appliance.days),  # Serialize list as JSON
                json.dumps(appliance.times)  # Serialize dict as JSON
            ))
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error inserting appliances: {str(e)}")

    db.commit()

    # Simulate data and save to CSV
    simulated_data = generate_simulated_data(appliances, weather_data)
    csv_file_path = save_data_to_csv(simulated_data)

    # Run prediction using the trained LightGBM model
    try:
        prediction_result = predict_energy_usage(csv_file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

    return {
        "prediction": prediction_result,
        "billAmount": calculate_bill_amount(prediction_result["predicted_energy"]),  # Fix: Pass only the list
        "recommendations": get_recommendations(prediction_result)
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

# Helper functions



# Appliance name mapping
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
    "visibility": 10000,
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

def generate_simulated_data(appliances, weather_data):
    """Generates simulated energy consumption data for 90 days based on user appliances and weather."""
    
    simulated_data = []
    today = datetime.now()

    # Ensure weather_data is valid
    weather_data = weather_data or {}
    
    for i in range(90):  # Generate data for 90 days
        current_date = today - timedelta(days=i)
        month, day, hour, weekday = current_date.month, current_date.day, current_date.hour, current_date.weekday()

        # Initialize row with 0s for all appliances
        row = {name: 0.0 for name in appliance_mapping.values()}

        print(f"\nProcessing Data for {current_date.strftime('%Y-%m-%d %H:%M')}:")  # Debugging log

        # Process each appliance
        for frontend_name, appliance_data in appliances.items():
            dataset_name = appliance_mapping.get(frontend_name.strip())
            print(f"  - Appliance: {frontend_name} (Mapped: {dataset_name})")

            # Convert Pydantic model to dictionary if needed
            if hasattr(appliance_data, "model_dump"):  
                appliance_data = appliance_data.model_dump()  # Pydantic v2
            elif hasattr(appliance_data, "dict"):  
                appliance_data = appliance_data.dict()  # Pydantic v1

            if dataset_name and isinstance(appliance_data, dict):
                print(f"✅ Entering IF condition for: {frontend_name}")  # Debugging
                try:
                    usage_hours = float(appliance_data.get("usageTime", "0h").replace("h", "").strip())
                except ValueError:
                    usage_hours = 0.0  # Handle invalid usageTime

                power_rating = float(appliance_data.get("power", 0))  # Ensure power is float
                print(f"    Power: {power_rating} kW, Usage Hours: {usage_hours}")

                # Calculate simulated energy usage with random variation
                base_usage = usage_hours * power_rating * random.uniform(0.8, 1.2)
                print(f"    Base Usage: {base_usage:.2f} kWh")

                # Adjust based on temperature (higher temps increase AC usage, for example)
                temperature = weather_data.get("temperature", default_weather["temperature"])
                adjusted_usage = base_usage * (temperature / 300)

                # Adjust for specific time of usage
                for time_range in appliance_data.get("times", {}).values():
                    if is_valid_usage_time(hour, time_range):
                        adjusted_usage *= random.uniform(0.9, 1.1)  # Small variation

                row[dataset_name] = round(adjusted_usage, 2)  # Store rounded values
            else:
                print(f"❌ Skipping {frontend_name} (dataset_name={dataset_name}, appliance_data={appliance_data})")
                print(f"Type of appliance_data: {type(appliance_data)}")
                print(f"appliance_data attributes: {dir(appliance_data)}")  # Debugging

        # Add weather data to the row
        row.update({
            "temperature": weather_data.get("temperature", default_weather["temperature"]),
            "humidity": weather_data.get("humidity", default_weather["humidity"]),
            "visibility": weather_data.get("visibility", default_weather["visibility"]),
            "pressure": weather_data.get("pressure", default_weather["pressure"]),
            "windSpeed": weather_data.get("windSpeed", default_weather["windSpeed"]),
            "cloudCover": weather_data.get("cloudCover", default_weather["cloudCover"]),
            "windBearing": weather_data.get("windBearing", default_weather["windBearing"]),
            "precipIntensity": weather_data.get("precipIntensity", default_weather["precipIntensity"]),
            "precipProbability": weather_data.get("precipProbability", default_weather["precipProbability"]),
            "month": month,
            "day": day,
            "hour": hour,
            "weekday": weekday
        })

        # Debugging Row Data
        print(f"Final row data: {row}\n")

        simulated_data.append(row)

    return simulated_data

def save_data_to_csv(data):
    """Saves the simulated data to a CSV file."""
    file_path = "simulated_data.csv"
    with open(file_path, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=list(data[0].keys()))
        writer.writeheader()
        writer.writerows(data)
    print(f"CSV saved successfully: {file_path}")  # Debugging Log
    return file_path




def calculate_bill_amount(predictions):
    max_energy = 14.714567  # Max energy for denormalization

    # Debug: Print raw prediction data
    print("Raw Prediction Data:", predictions)
    print("🔍 Received data type:", type(predictions))  # Debugging print

    if isinstance(predictions, dict):
        print("🔍 Dictionary Keys:", predictions.keys())  # Check what keys exist

    if isinstance(predictions, pd.DataFrame):
        print("🔍 DataFrame Preview:\n", predictions.head())  # Show sample data

    if not isinstance(predictions, list):
        raise ValueError(f"Error: Expected a list of dictionaries but got {type(predictions)}.")

    # Ensure the predictions data is a list
    if not isinstance(predictions, list):
        raise ValueError("Error: Expected a list of dictionaries but got something else.")

    # Convert predictions list into a DataFrame
    predicted_energy = pd.DataFrame(predictions)

    # Debug: Print DataFrame after conversion
    print("Converted DataFrame:\n", predicted_energy.head())

    # Ensure required columns exist
    if "predicted_use" not in predicted_energy.columns:
        raise ValueError("Error: 'predicted_use' column is missing in prediction data.")

    if "date" in predicted_energy.columns:
        predicted_energy["date"] = pd.to_datetime(predicted_energy["date"])
        predicted_energy["month"] = predicted_energy["date"].dt.month
    else:
        print("Warning: 'date' column missing in prediction data, using current month.")
        predicted_energy["month"] = datetime.now().month  # Default to current month

    # Denormalize predicted energy consumption
    predicted_energy["predicted_use"] *= max_energy

    # Group by month to calculate total energy consumption per month
    monthly_consumption = predicted_energy.groupby("month")["predicted_use"].sum()

    # Function to calculate the bill for a given month's consumption
    def calculate_bill(units, phase="single"):
        if units <= 500:
            energy_cost = units * 7.60  # ₹7.60 per unit for ≤ 500 kWh
        else:
            energy_cost = (500 * 7.60) + ((units - 500) * 8.70)  # ₹8.70 per unit for > 500 kWh

        fixed_charge = 50 if phase == "single" else 125  # ₹50 for single-phase, ₹125 for three-phase
        electricity_duty = units * 0.06  # ₹0.06 per unit duty

        total_bill = energy_cost + fixed_charge + electricity_duty
        return total_bill

    # Calculate the bill for each month
    bill_summary = {month: calculate_bill(units) for month, units in monthly_consumption.items()}

    # Compute the total bill for the next 3 months
    total_bill = sum(bill_summary.values())

    # Convert month numbers to names
    month_names = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun", 
                   7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}

    # Convert to DataFrame for easy readability
    bill_df = pd.DataFrame(list(bill_summary.items()), columns=["Month", "Bill Amount (₹)"])
    bill_df["Month"] = bill_df["Month"].map(month_names)

    print("Final Bill Summary:")
    print(bill_df)

    return {
        "monthly_bills": bill_summary,
        "total_bill": total_bill
    }




def get_recommendations(feature_data, model):
    try:
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

        # Generate recommendations based on high-impact features
        recommendations = []
        for feature, impact in sorted_features[:3]:  # Top 3 influential features
            if "AC" in feature:
                recommendations.append("Your AC usage is high. Reduce usage or use energy-efficient settings.")
            elif "Heater" in feature:
                recommendations.append("Consider using a thermostat or energy-efficient heating solutions.")
            elif "PeakHours" in feature:
                recommendations.append("Shift some appliance usage to non-peak hours to save on electricity bills.")
            else:
                recommendations.append(f"Optimize your usage of {feature} to lower energy consumption.")

        return recommendations

    except Exception as e:
        return [f"Error generating recommendations: {str(e)}"]
