from pydantic import BaseModel, Field
from typing import Optional
from beanie import Document

class CarModel(Document):
    make: str = Field(..., description="The company that made the car")
    model: str = Field(..., description="The model name")                                                                                                                                                        
    year: int = Field(..., description="What year the car was made")
    mileage: Optional[int] = Field(None, description="Current mileage of the vehicle")                                                                                                                           
    vin: Optional[str] = Field(None, description="Vehicle Identification Number")                                                                                                                                
   
    class Settings:                                                                                                                                                                                              
        name = "cars"  