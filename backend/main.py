from fastapi import FastAPI, HTTPException
from backend.database import engine, Base
from backend.routers import appliances, weather, recommendations, billing, prediction

app = FastAPI(title="Energy Consumption Prediction API")

# Initialize the database tables
Base.metadata.create_all(bind=engine)

# Include all routers
app.include_router(recommendations.router, prefix="/api/recommend")
app.include_router(appliances.router, prefix="/api/appliances")
app.include_router(weather.router, prefix="/api/weather")
app.include_router(prediction.router, prefix="/api/predict")
app.include_router(billing.router, prefix="/api/billing")

@app.get("/")
def home():
    return {"message": "Welcome to Energy Prediction API"}

