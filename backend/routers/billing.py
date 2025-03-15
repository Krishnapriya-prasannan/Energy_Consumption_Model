import requests
import os
import csv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# Load tariff rates (if using fixed sample rates)
TARIFF_RATES = {
    "default": 0.12,  # Default rate per kWh (example: 12 cents per kWh)
    "IN": 0.10,       # Example: India rate per kWh
    "US": 0.15,        # Example tariff rate for the US
    "EU": 0.20         # Example rate for Europe
}

# API Key for web scraping (if required)
SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY")  # Load from .env file

class BillingRequest(BaseModel):
    location: str
    csv_path: str  # Path to the CSV file containing predicted consumption

def get_tariff_rate(location: str) -> float:
    """Fetch tariff rate based on user location using API, Web Scraping, or fixed rates."""
    try:
        # Example: Call a tariff API (if available for free)
        api_url = f"https://api.example.com/tariffs?location={location}&apikey={SCRAPER_API_KEY}"
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            return data.get("tariff", TARIFF_RATES["default"])
        else:
            # If API is unavailable, use default/fixed rates
            return TARIFF_RATES.get(location, TARIFF_RATES["default"])
    except Exception as e:
        print(f"Tariff API failed: {str(e)}")
        return TARIFF_RATES["default"]

@router.post("/billing")
def generate_bill(data: BillingRequest):
    """
    Generate an estimated energy bill based on the predicted energy consumption
    and tariff rates.
    """
    try:
        # Read predicted energy consumption from the CSV file
        if not os.path.exists(data.csv_file):
            raise HTTPException(status_code=404, detail="CSV file not found")

        total_consumption = 0.0
        with open(data.csv_path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(csvfile)  # Skip header row
            for row in csvfile:
                total_consumption += float(row[1])  # Assuming consumption is in the second column

        # Get the tariff rate for the location
        tariff_rate = get_tariff_rate(data.location)

        # Calculate the estimated bill
        estimated_bill = total_consumption * tariff_rate

        return {
            "location": data.location,
            "total_energy_consumption_kWh": total_consumption,
            "tariff_rate_per_kWh": tariff_rate,
            "estimated_bill": estimated_bill
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Billing error: {str(e)}")
