from fastapi import APIRouter, HTTPException
from typing import List
from backend.models.car_model import CarModel
from backend.database import get_car_collection


router = APIRouter(prefix="/cars", tags=["Cars"])

@router.post("/", response_model=CarModel, status_code=201)                                                                                                                                                      
async def add_car(car: CarModel):
      if car.initial_mileage is None and car.mileage is not None:
            car.initial_mileage = car.mileage
      await car.insert()
      return car                                                                                                                                                                                                   
   
@router.get("/", response_model=List[CarModel])                                                                                                                                                                  
async def get_cars():                                 
      return await CarModel.find_all().to_list()

@router.get("/{car_id}", response_model=CarModel)
async def get_car(car_id: str):
      car = await CarModel.get(car_id)
      if not car:
            raise HTTPException(status_code=404, detail="Car not found")
      return car

@router.delete("/{car_id}", status_code=204)
async def delete_car(car_id: str):
      car = await CarModel.get(car_id)
      if not car:
            raise HTTPException(status_code=404, detail="Car not found")
      await car.delete()

@router.patch("/{car_id}", response_model=CarModel)
async def update_car(car_id: str, car_data: CarModel):
      car = await CarModel.get(car_id)
      if not car:
            raise HTTPException(status_code=404, detail="Car not found")
      
      update_data = car_data.model_dump(exclude_unset=True)
      if not update_data:
            raise HTTPException(status_code=400, detail="No fields provided for update")
      
      await car.update({"$set": update_data})
      updated_car = await CarModel.get(car_id)
      return updated_car