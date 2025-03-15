from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Appliance
from pydantic import BaseModel
from typing import List

router = APIRouter(
    prefix="/appliances",
    tags=["Appliances"]
)

# Schema for incoming appliance data
class ApplianceCreate(BaseModel):
    name: str
    power: float  # Power consumption in kW
    usage_hours: float
    usage_days: list[str]
    peak_time: str
    location: str

# API to add a new appliance usage
@router.post("/")
def add_appliance(appliance: ApplianceCreate, db: Session = Depends(get_db)):
    new_appliance = models.Appliance(
        name=appliance.name,
        usage_hours=appliance.usage_hours,
        usage_days=appliance.usage_days,
        peak_time=appliance.peak_time,
        location=appliance.location
    )
    db.add(new_appliance)
    db.commit()
    db.refresh(new_appliance)
    return {"message": "Appliance added successfully", "appliance_id": new_appliance.id}

# API to get all appliances
@router.get("/", response_model=List[ApplianceCreate])
def get_appliances(db: Session = Depends(get_db)):
    return db.query(models.Appliance).all()
