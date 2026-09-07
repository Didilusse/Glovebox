from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from typing import List
from backend.auth import ensure_car_owner_active, get_current_user, get_owned_car
from backend.models.car_model import CarCreate, CarModel, CarResponse, CarUpdate
from backend.models.maintenance_log import MaintenanceLog
from backend.models.mod import ModItem
from backend.models.user import User


router = APIRouter(prefix="/cars", tags=["Cars"])

@router.post("/", response_model=CarResponse, status_code=201)
async def add_car(car_data: CarCreate, user: User = Depends(get_current_user)):
      data = car_data.model_dump()
      if data["initial_mileage"] is None and data["mileage"] is not None:
            data["initial_mileage"] = data["mileage"]
      car = CarModel(owner_id=user.id, **data)
      await car.insert()
      await ensure_car_owner_active(car)
      return car

@router.get("/", response_model=List[CarResponse])
async def get_cars(
      user: User = Depends(get_current_user),
      skip: int = Query(0, ge=0),
      limit: int = Query(100, ge=1, le=100),
):
      return await CarModel.find(CarModel.owner_id == user.id).sort(CarModel.id).skip(skip).limit(limit).to_list()

@router.get("/{car_id}", response_model=CarResponse)
async def get_car(car: CarModel = Depends(get_owned_car)):
      return car

@router.delete("/{car_id}", status_code=204)
async def delete_car(
    car: CarModel = Depends(get_owned_car),
):
      #print(f"DEBUG: Attempting to delete car with ID: {car.id}")

      await car.update({"$set": {"is_deleting": True}})
      await MaintenanceLog.find(MaintenanceLog.car_id == car.id).delete()
      await ModItem.find(ModItem.car_id == car.id).delete()
      await car.delete()

      return None

@router.patch("/{car_id}", response_model=CarResponse)
async def update_car(car_data: CarUpdate, car: CarModel = Depends(get_owned_car)):
      update_data = car_data.model_dump(exclude_unset=True)
      if not update_data:
            raise HTTPException(status_code=400, detail="No fields provided for update")

      await car.update({"$set": update_data})
      return await CarModel.get(car.id)
