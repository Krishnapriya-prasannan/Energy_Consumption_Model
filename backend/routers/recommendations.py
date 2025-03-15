import os
import json
import pickle
import lightgbm as lgb
import pandas as pd
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Recommendation
from pydantic import BaseModel

router = APIRouter()

# Load the pre-trained LightGBM model from a .pkl file
MODEL_PATH = "./lightgbm_model3.pkl"

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")

with open(MODEL_PATH, "rb") as file:
    model = pickle.load(file)

class RecommendationRequest(BaseModel):
    location: str  

@router.post("/")
def get_recommendations(data: RecommendationRequest, db: Session = Depends(get_db)):
    try:
        csv_path = "./denormalized_dataset.csv"

        # Validate if CSV file exists
        if not os.path.exists(csv_path):
            raise HTTPException(status_code=400, detail=f"CSV file not found at {csv_path}")

        # Load CSV data
        df = pd.read_csv(csv_path)

        # Required features for prediction
        feature_columns = [
    "Dishwasher", "AirConditioner", "Heater", "ComputerDevices", "Refrigerator",
    "WashingMachine", "Fans", "Chimney", "FoodProcessor", "InductionCooktop",
    "Lights", "WaterPump", "Microwave", "TV",
    "temperature", "humidity", "visibility", "pressure", "windSpeed",
    "cloudCover", "windBearing", "precipIntensity", "precipProbability",
    "month", "day", "hour", "weekday"
]

        # Ensure all required columns exist
        missing_columns = [col for col in feature_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(status_code=400, detail=f"Missing columns: {missing_columns}")

        # Preprocess data: select columns, fill missing values, and convert to float
        df = df[feature_columns].fillna(0).astype(float)

        # Predict energy usage
        predictions = model.predict(df)

        # Generate recommendations
        recommendations = []
        for idx, expected_usage in enumerate(predictions):
            actual_usage = df["Dishwasher"].iloc[idx]  # Example: Comparing with dishwasher usage

            if expected_usage > actual_usage:
                advice = "Consider reducing energy usage during peak hours."
            else:
                advice = "Your energy consumption is efficient."

            recommendations.append({
                "date": f"{int(df['day'].iloc[idx])}/{int(df['month'].iloc[idx])}",
                "expected_usage": expected_usage,
                "actual_usage": actual_usage,
                "advice": advice
            })

        # Save recommendations to the database
        rec_data = Recommendation(
            location=data.location,  # ✅ Matches the database schema
            recommendation_text=json.dumps(recommendations)  # ✅ Correct column name
        )
        db.add(rec_data)
        db.commit()
        db.refresh(rec_data)  # ✅ Ensure the data is committed properly

        print("Inserted:", rec_data.id)  # ✅ Debugging: Print inserted record ID

        return {"message": "Recommendations generated!", "data": recommendations}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
