import os
import pickle
import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# Load the trained model
MODEL_PATH = "./lightgbm_model3.pkl"

try:
    with open(MODEL_PATH, "rb") as model_file:
        model = pickle.load(model_file)
except Exception as e:
    raise RuntimeError(f"Error loading model: {str(e)}")

# Define the correct request model
class PredictionRequest(BaseModel):
    Dishwasher: float
    AirConditioner: float
    Heater: float
    ComputerDevices: float
    Refrigerator: float
    WashingMachine: float
    Fans: float
    Chimney: float
    FoodProcessor: float
    InductionCooktop: float
    Lights: float
    WaterPump: float
    Microwave: float
    TV: float
    temperature: float
    humidity: float
    visibility: float
    pressure: float
    windSpeed: float
    cloudCover: float
    windBearing: float
    precipIntensity: float
    precipProbability: float
    month: int
    day: int
    hour: int
    weekday: int

    

@router.post("/")
def predict_energy_consumption(data: PredictionRequest):
    """Predict energy consumption based on input data."""
    try:
        # Convert input data into numpy array
        input_data = np.array([[ 
            data.Dishwasher, data.AirConditioner, data.Heater, data.ComputerDevices,
            data.Refrigerator, data.WashingMachine, data.Fans, data.Chimney,
            data.FoodProcessor, data.InductionCooktop, data.Lights, data.WaterPump,
            data.Microwave, data.TV, data.temperature, data.humidity,
            data.visibility, data.pressure, data.windSpeed, data.cloudCover,
            data.windBearing, data.precipIntensity, data.precipProbability,
            data.month, data.day, data.hour, data.weekday
        ]])

        # Make prediction
        prediction = model.predict(input_data)

        return {"predicted_energy_consumption": prediction.tolist()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")