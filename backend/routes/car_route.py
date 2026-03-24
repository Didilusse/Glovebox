from fastapi import APIRouter
from typing import List
from backend.models.car_model import CarModel
from backend.database import get_car_collection

router = APIRouter(prefix="/cars", tags=["Cars"])

@router.post("/", response_model=CarModel, status_code=201)
async def add_car(car: CarModel):
    car_collection = get_car_collection()
    car_dict = car.model_dump()
    new_car = await car_collection.insert_one(car_dict)
    
    created_car = await car_collection.find_one({"_id": new_car.inserted_id})
    return created_car

@router.get("/", response_model=List[CarModel])
async def get_cars():
    car_collection = get_car_collection()
    cars = await car_collection.find().to_list(length=100)
    return cars