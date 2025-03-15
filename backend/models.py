from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

class Appliance(Base):
    __tablename__ = "appliances"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    power_rating = Column(Float)
    count = Column(Integer)
    usage_hours = Column(Float)
    usage_days = Column(String(255))
    time_of_usage = Column(String(255))
    location = Column(String(255))

class WeatherData(Base):
    __tablename__ = "weather_data"
    id = Column(Integer, primary_key=True, index=True)
    location = Column(String(255))
    temperature = Column(Float)
    humidity = Column(Float)
    wind_speed = Column(Float)

class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, index=True)
    location = Column(String(255))
    prediction_csv = Column(String(255))  # Store CSV file path

class Bill(Base):
    __tablename__ = "bills"
    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id"))
    bill_amount = Column(Float)
    tariff_source = Column(String(255))


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    location = Column(String(255))
    recommendation_text = Column(String(1000))  # ✅ Matches the API insertion
