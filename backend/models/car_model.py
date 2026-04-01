from pydantic import Field, BaseModel
from typing import Optional
from datetime import date
from enum import Enum
from beanie import Document


class FuelType(str, Enum):
    gas = "gas"
    diesel = "diesel"
    electric = "electric"


class CarModel(Document):
    make: str = Field(..., description="The company that made the car")
    model: str = Field(..., description="The model name")
    year: int = Field(..., description="What year the car was made")
    mileage: Optional[int] = Field(None, description="Current mileage of the vehicle")
    initial_mileage: Optional[int] = Field(None, description="Odometer reading when the car was added")
    vin: Optional[str] = Field(None, description="Vehicle Identification Number")
    license_plate: Optional[str] = Field(None, description="License plate number")
    fuel_type: Optional[FuelType] = Field(None, description="Fuel type: gas, diesel, or electric")
    purchased_date: Optional[date] = Field(None, description="Date the vehicle was purchased")
    purchased_price: Optional[float] = Field(None, description="Price paid for the vehicle")

    class Settings:
        name = "cars"