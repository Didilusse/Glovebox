from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from backend.auth import ensure_car_owner_active, get_current_user, get_owned_car
from backend.auth import car_response, get_vehicle_car
from backend.models.car_share import CarShare, ShareCreate, ShareUpdate, ShareResponse
from pymongo.errors import DuplicateKeyError
from backend.models.car_model import CarCreate, CarModel, CarResponse, CarUpdate
from backend.models.maintenance_log import MaintenanceLog
from backend.models.notification import Notification
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
      return await car_response(car, user)

@router.get("/", response_model=List[CarResponse])
async def get_cars(
      user: User = Depends(get_current_user),
      skip: int = Query(0, ge=0),
      limit: int = Query(100, ge=1, le=100),
):
      grants = await CarShare.find(CarShare.user_id == user.id).to_list()
      shared_cars = await CarModel.find({"_id": {"$in": [grant.car_id for grant in grants]}}).to_list()
      active_owners = await User.find({
            "_id": {"$in": [user.id, *{car.owner_id for car in shared_cars}]},
            "is_deleting": {"$ne": True},
      }).to_list()
      cars = await CarModel.find({
            "is_deleting": {"$ne": True},
            "owner_id": {"$in": [owner.id for owner in active_owners]},
            "$or": [{"owner_id": user.id}, {"_id": {"$in": [grant.car_id for grant in grants]}}],
      }).sort(CarModel.id).skip(skip).limit(limit).to_list()
      return [await car_response(car, user) for car in cars]

@router.get("/{car_id}", response_model=CarResponse)
async def get_car(car: CarModel = Depends(get_vehicle_car), user: User = Depends(get_current_user)):
      return await car_response(car, user)

@router.delete("/{car_id}", status_code=204)
async def delete_car(
    car: CarModel = Depends(get_owned_car),
):
      #print(f"DEBUG: Attempting to delete car with ID: {car.id}")

      await car.update({"$set": {"is_deleting": True}})
      await MaintenanceLog.find(MaintenanceLog.car_id == car.id).delete()
      await Notification.find(Notification.car_id == car.id).delete()
      await ModItem.find(ModItem.car_id == car.id).delete()
      await CarShare.find(CarShare.car_id == car.id).delete()
      await car.delete()

      return None

@router.patch("/{car_id}", response_model=CarResponse)
async def update_car(car_data: CarUpdate, car: CarModel = Depends(get_vehicle_car), user: User = Depends(get_current_user)):
      update_data = car_data.model_dump(exclude_unset=True)
      if not update_data:
            raise HTTPException(status_code=400, detail="No fields provided for update")

      await car.update({"$set": update_data})
      return await car_response(car, user)


@router.get("/{car_id}/shares/", response_model=List[ShareResponse])
async def list_shares(car: CarModel = Depends(get_owned_car)):
      grants = await CarShare.find(CarShare.car_id == car.id).sort(CarShare.id).to_list()
      result = []
      for grant in grants:
            recipient = await User.get(grant.user_id)
            if recipient and not recipient.is_deleting:
                  result.append(ShareResponse(id=grant.id, user_id=grant.user_id, username=recipient.username, permissions=grant.permissions))
      return result


async def ensure_share_active(grant: CarShare, car: CarModel):
      # A deletion cascade may have passed before this in-flight grant was inserted.
      current_car = await CarModel.get(car.id)
      owner = await User.get(car.owner_id)
      recipient = await User.get(grant.user_id)
      if not current_car or current_car.is_deleting or not owner or owner.is_deleting or not recipient or recipient.is_deleting:
            await grant.delete()
            raise HTTPException(404, "Car or recipient not found")
      return ShareResponse(id=grant.id, user_id=grant.user_id, username=recipient.username, permissions=grant.permissions)


@router.post("/{car_id}/shares/", response_model=ShareResponse, status_code=201)
async def create_share(payload: ShareCreate, car: CarModel = Depends(get_owned_car)):
      recipient = await User.find_one(User.username == payload.username)
      if not recipient or recipient.is_deleting:
            raise HTTPException(404, "User not found")
      if recipient.id == car.owner_id:
            raise HTTPException(400, "Cannot share a vehicle with yourself")
      grant = CarShare(car_id=car.id, user_id=recipient.id, permissions=payload.permissions)
      try:
            await grant.insert()
      except DuplicateKeyError:
            raise HTTPException(409, "Vehicle already shared with this user") from None
      return await ensure_share_active(grant, car)


@router.put("/{car_id}/shares/{user_id}", response_model=ShareResponse)
async def update_share(user_id: PydanticObjectId, payload: ShareUpdate, car: CarModel = Depends(get_owned_car)):
      grant = await CarShare.find_one({"car_id": car.id, "user_id": user_id})
      if not grant:
            raise HTTPException(404, "Share not found")
      # Never upsert: an update racing revocation must not resurrect the grant.
      result = await CarShare.get_pymongo_collection().update_one(
            {"_id": grant.id}, {"$set": {"permissions": payload.permissions.model_dump()}}
      )
      if not result.matched_count:
            raise HTTPException(404, "Share not found")
      grant.permissions = payload.permissions
      return await ensure_share_active(grant, car)


@router.delete("/{car_id}/shares/{user_id}", status_code=204)
async def delete_share(user_id: PydanticObjectId, car: CarModel = Depends(get_owned_car)):
      grant = await CarShare.find_one({"car_id": car.id, "user_id": user_id})
      if not grant:
            raise HTTPException(404, "Share not found")
      await grant.delete()
