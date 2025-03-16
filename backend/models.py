from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.orm import relationship
from backend.database import Base
from sqlalchemy import JSON

class Appliance(Base):
    __tablename__ = 'appliances'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    power_rating = Column(Float)
    count = Column(Integer)
    usage_hours = Column(Float)
    usage_days = Column(String)  # You can store a list of days or comma-separated values
    time_of_usage = Column(JSON)  # Stores the times as a JSON object or array
    location = Column(String)

    appliance_usage = relationship("ApplianceUsage", back_populates="appliance")

class ApplianceUsage(Base):
    __tablename__ = 'appliance_usage'

    id = Column(Integer, primary_key=True, index=True)
    appliance_id = Column(Integer, ForeignKey("appliances.id"))
    usage_date = Column(Date)
    usage_hour = Column(Integer)  # Hour of the day when the appliance was used
    usage_duration = Column(Float)  # Duration of usage in hours

    appliance = relationship("Appliance", back_populates="appliance_usage")


class Location(Base):
    __tablename__ = 'locations'

    id = Column(Integer, primary_key=True, index=True)
    location_name = Column(String, index=True)  # Can store a name or latitude/longitude

    weather_data = relationship("WeatherData", back_populates="location")

class WeatherData(Base):
    __tablename__ = 'weather_data'

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"))
    temperature = Column(Float)
    humidity = Column(Float)
    wind_speed = Column(Float)
    visibility = Column(Float)
    pressure = Column(Float)
    cloud_cover = Column(Float)
    wind_bearing = Column(Integer)
    precip_intensity = Column(Float)
    precip_probability = Column(Float)
    month = Column(Integer)
    day = Column(Integer)
    hour = Column(Integer)
    weekday = Column(Integer)

    location = relationship("Location", back_populates="weather_data")

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
