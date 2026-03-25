from fastapi import APIRouter
from typing import List
from backend.models.car_model import CarModel
from backend.database import get_car_collection


router = APIRouter(prefix="/cars", tags=["Cars"])

@router.post("/", response_model=CarModel, status_code=201)                                                                                                                                                      
async def add_car(car: CarModel):                     
      await car.insert()
      return car                                                                                                                                                                                                   
   
@router.get("/", response_model=List[CarModel])                                                                                                                                                                  
async def get_cars():                                 
      return await CarModel.find_all().to_list()