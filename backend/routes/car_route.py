from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, Path, Query
from typing import List
from backend.models.car_model import CarCreate, CarModel, CarResponse, CarUpdate
from backend.models.maintenance_log import MaintenanceLog
from backend.models.mod import ModItem


router = APIRouter(prefix="/cars", tags=["Cars"])

@router.post("/", response_model=CarResponse, status_code=201)
async def add_car(car_data: CarCreate):
      data = car_data.model_dump()
      if data["initial_mileage"] is None and data["mileage"] is not None:
            data["initial_mileage"] = data["mileage"]
      car = CarModel(**data)
      await car.insert()
      return car
   
@router.get("/", response_model=List[CarResponse])
async def get_cars(
      skip: int = Query(0, ge=0),
      limit: int = Query(100, ge=1, le=100),
):
      return await CarModel.find_all().sort(CarModel.id).skip(skip).limit(limit).to_list()

@router.get("/{car_id}", response_model=CarResponse)
async def get_car(car_id: PydanticObjectId):
      car = await CarModel.get(car_id)
      if not car:
            raise HTTPException(status_code=404, detail="Car not found")
      return car

@router.delete("/{car_id}", status_code=204)
async def delete_car(
    car_id: PydanticObjectId = Path(..., description="The ID of the car to delete")
):
      car = await CarModel.get(car_id)
      
      #print(f"DEBUG: Attempting to delete car with ID: {car_id}")
      if not car:
        raise HTTPException(
            status_code=404, 
            detail=f"Car with ID {car_id} not found"
        )
    
      await car.update({"$set": {"is_deleting": True}})
      await MaintenanceLog.find(MaintenanceLog.car_id == car_id).delete()
      await ModItem.find(ModItem.car_id == car_id).delete()
      await car.delete()
        
      return None 

@router.patch("/{car_id}", response_model=CarResponse)
async def update_car(car_id: PydanticObjectId, car_data: CarUpdate):
      car = await CarModel.get(car_id)
      if not car:
            raise HTTPException(status_code=404, detail="Car not found")
      
      update_data = car_data.model_dump(exclude_unset=True)
      if not update_data:
            raise HTTPException(status_code=400, detail="No fields provided for update")
      
      await car.update({"$set": update_data})
      return await CarModel.get(car_id)
