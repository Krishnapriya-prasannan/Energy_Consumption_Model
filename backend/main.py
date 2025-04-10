import os
import json
import mysql.connector
import requests
import csv
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, validator
from typing import Dict, List, Optional
from fastapi.middleware.cors import CORSMiddleware
import pickle
import pandas as pd
import numpy as np
from collections import defaultdict
import google.generativeai as genai
from dotenv import load_dotenv


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
load_dotenv()
KSEB_API_URL = os.getenv("KSEB_API_URL")
GENAI_API_KEY = os.getenv("GENAI_API_KEY")
API_URL = os.getenv("KSEB_BILL_URL")

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

class Appliance(BaseModel):
    power: float
    count: int
    usageTime: str  # Kept as string but converted later
    days: List[str]

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
        for name, appliance in v.items():
            if "usage" in appliance:
                print(f"Legacy 'usage' field detected in appliance: {name}")
                appliance["usageTime"] = appliance.pop("usage")
        return v

# Data Fetching Utilities
def fetch_past_consumption(consumer_id: str):
    try:
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        response = requests.post(KSEB_API_URL, headers=headers, data={"optionVal": consumer_id})
        print(f"API Response: {response.text}")  # Debugging log
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching consumption data: {str(e)}")

def format_consumption_data(consumption_data):
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

    return formatted_data
def fetch_historical_weather(location: str, start_date: str, end_date: str):
    try:
        # Parse location input

        print(f"start_date: {start_date}, end_date: {end_date}")  # Debugging log
        match = location.strip().split(", ")
        if len(match) != 2:
            raise ValueError("Invalid location format")

        lat, lon = match[0].split(":")[1], match[1].split(":")[1]

        # Convert start_date and end_date to previous year's same month and day
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        print(f"start_dt: {start_dt}, end_dt: {end_dt}")  # Debugging log
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
        temperatures = [temp if temp is not None else 0 for temp in hourly_data.get("temperature_2m", [0] * len(times))]
        humidities = [hum if hum is not None else 0 for hum in hourly_data.get("relative_humidity_2m", [0] * len(times))]
        visibilities = [vis if vis is not None else 0 for vis in hourly_data.get("visibility", [0] * len(times))]
        pressures = [pres if pres is not None else 0 for pres in hourly_data.get("surface_pressure", [0] * len(times))]
        wind_speeds = [wind if wind is not None else 0 for wind in hourly_data.get("wind_speed_10m", [0] * len(times))]
        cloud_covers = [cloud if cloud is not None else 0 for cloud in hourly_data.get("cloud_cover", [0] * len(times))]
        wind_bearings = [wind_bear if wind_bear is not None else 0 for wind_bear in hourly_data.get("wind_direction_10m", [0] * len(times))]
        precip_intensities = [precip if precip is not None else 0 for precip in hourly_data.get("precipitation", [0] * len(times))]
        precip_probabilities = [precip_prob if precip_prob is not None else 0 for precip_prob in hourly_data.get("precipitation_probability", [0] * len(times))]

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
        total_monthly_forecast = round(monthly_totals["predicted_use"].sum(), 2)

        print(f"Final Prediction Data: {full_prediction_df}")  # Debugging log
        print(f"Monthly Totals: {monthly_totals}")  # Debugging log
        print(f"All Dates: {all_dates}")  # Debugging log
        print(f"Total Monthly Forecast: {total_monthly_forecast}")  # Debugging log

        return {
            "totalEnergyUsage": total_energy_usage,
            "predicted_energy": full_prediction_df.to_dict(orient="records"),
            "monthly_forecast": monthly_totals.to_dict(orient="records"),
            "total_monthly_forecast": total_monthly_forecast,
            "all_dates": all_dates  # ✅ Includes all dates
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


def calculate_bill_amount(consumption_data, phase):
    if not isinstance(consumption_data, list):
        raise ValueError(f"Expected a list but got {type(consumption_data)}.")

    formatted_phase = str(phase).split('-')[0]
    bill_summary = {}
    total_bill = 0

    i = 0
    while i < len(consumption_data):
        if i + 1 < len(consumption_data):  # Bi-monthly
            units = consumption_data[i]["units"] + consumption_data[i + 1]["units"]
            frequency = 2
            i += 2
        else:  # One month left
            units = consumption_data[i]["units"]
            frequency = 1
            i += 1

        payload = {
            "tariff_id": 1,
            "purpose_id": 15,
            "frequency": frequency,
            "WNL": max(int(units), 0),
            "phase": formatted_phase
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        month = consumption_data[0]["month"]

        try:
            response = requests.post(API_URL, headers=headers, data=payload)
            response.raise_for_status()
            data = response.json()

            if data.get("err_flag") == 0 and "result_data" in data:
                bill_value = data["result_data"].get("tariff_values", {}).get("bill_total", {}).get("value", 0)
                bill_summary[month] = bill_value
                total_bill += bill_value
            else:
                bill_summary[month] = 0
        except requests.RequestException as e:
            bill_summary[month] = 0

    print(f"Total Bill: {total_bill}")
    return total_bill



def get_recommendations(predicted_energy, past_consumption, appliances):
    try:
        if not GENAI_API_KEY:
            return ["Error: Missing GenAI API key. Check your .env file."]

        # Configure GenAI with API key
        genai.configure(api_key=GENAI_API_KEY) #Sets up the GenAI library using your API key to authenticate.

        
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
            predicted_energy = sum(d["predicted_use"] for d in predicted_energy) 
        elif isinstance(predicted_energy, list) and not predicted_energy:
            return ["Error: No predicted energy data provided."]
        elif not isinstance(predicted_energy, (int, float)):
            return ["Error: predicted_energy should be a number or a list of dictionaries with 'predicted_use'."]

        # Generate structured prompt for GenAI
        prompt = f"""
Predicted energy usage: {predicted_energy:.2f} kWh

Past Energy Consumption Data:
{past_consumption.to_string(index=False)}

User's Appliances: {", ".join(appliances)}

Provide 3-4 short and specific recommendations, including:
- Appliance optimization strategies  
- General energy-saving tips  
- Suggestions based on comparing past consumption with predicted energy usage   

Avoid unnecessary formatting, symbols or emojis,also no need of bold.
"""


        # Call the best available Google GenAI model
        model = genai.GenerativeModel("models/gemini-2.0-flash-001")
        response = model.generate_content(prompt)
        print(f"GenAI Response: {response}")  # Debugging log   
        # Clean the response by removing checkmarks and unnecessary symbols
        if response.text:
            formatted_response = response.text.replace("✅", "").replace("✔️", "").replace("❌", "").strip()
            # Return the response as a list of recommendations
            return [line.strip() for line in formatted_response.split("\n") if line.strip()]
        else:
            return ["No recommendations received."]
    
    except Exception as e:
        return [f"Error generating recommendations: {str(e)}"]

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
    total_monthly_forecast = prediction_result.get("total_monthly_forecast", 0)
    print(f"appliances:{request.appliances}")
    print(f"consumption data :{consumption_data}")
   

    return {
        "prediction": prediction_result,
        "totalMonthlyForecast": total_monthly_forecast,
        "billAmount": calculate_bill_amount(
            consumption_data, 
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


