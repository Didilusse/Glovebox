from pydantic import BaseModel, Field
from typing import Optional

class CarModel(BaseModel):
    make: str = Field(..., description="The company that made the car")
    model: str = Field(..., description="The model name")
    year: int = Field(..., description="What year the car was made")
    
    mileage: Optional[int] = Field(None, description="Current mileage of the vehicle")
    vin: Optional[str] = Field(None, description="Vehicle Identification Number")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "make": "Mazda",
                    "model": "Miata",
                    "year": 1999,
                    "mileage": 105000,
                    "vin": "JM1NB353X00000000"
                }
            ]
        }
    }