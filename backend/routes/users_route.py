from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from beanie import PydanticObjectId
from pymongo.errors import DuplicateKeyError
from starlette.concurrency import run_in_threadpool

from backend.auth import hash_password, require_admin
from backend.models.car_model import CarModel
from backend.models.car_share import CarShare
from backend.models.maintenance_log import MaintenanceLog
from backend.models.mod import ModItem
from backend.models.session import AuthSession
from backend.models.notification import Notification, UserPreferences
from backend.models.user import PasswordReset, User, UserCreate, UserResponse

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(require_admin)],
)


@router.get("/", response_model=List[UserResponse])
async def list_users():
    return await User.find_all().sort(User.created_at, User.id).to_list()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate):
    normalized = payload.username.strip().lower()
    if await User.find_one(User.username == normalized):
        raise HTTPException(status_code=409, detail="Username is already taken")

    user = User(username=normalized, password_hash=await run_in_threadpool(hash_password, payload.password))
    try:
        await user.insert()
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Username is already taken") from None
    return user


@router.patch("/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_user_password(user_id: PydanticObjectId, payload: PasswordReset):
    user = await User.get(user_id)
    if not user or user.is_deleting:
        raise HTTPException(status_code=404, detail="User not found")

    password_hash = await run_in_threadpool(hash_password, payload.new_password)
    result = await User.get_pymongo_collection().update_one(
        {"_id": user_id, "is_deleting": {"$ne": True}},
        {"$set": {"password_hash": password_hash}, "$inc": {"credential_version": 1}},
    )
    if not result.matched_count:
        raise HTTPException(status_code=404, detail="User not found")
    await AuthSession.find(
        AuthSession.user_id == user_id,
        {"$or": [{"credential_version": {"$lte": user.credential_version}}, {"credential_version": {"$exists": False}}]},
    ).delete()


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: PydanticObjectId, current_user: User = Depends(require_admin)):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")
    if user.is_admin:
        raise HTTPException(status_code=400, detail="Administrator accounts cannot be deleted")

    # Disable first. A failed cascade can be retried without allowing new logins.
    result = await User.get_pymongo_collection().update_one(
        {"_id": user_id}, {"$set": {"is_deleting": True}, "$inc": {"credential_version": 1}}
    )
    if not result.matched_count:
        return
    cars = await CarModel.find(CarModel.owner_id == user_id).to_list()
    for car in cars:
        await CarModel.get_pymongo_collection().update_one(
            {"_id": car.id}, {"$set": {"is_deleting": True}}
        )
        await MaintenanceLog.find(MaintenanceLog.car_id == car.id).delete()
        await ModItem.find(ModItem.car_id == car.id).delete()
        await CarShare.find(CarShare.car_id == car.id).delete()
        await car.delete()

    await AuthSession.find(AuthSession.user_id == user_id).delete()
    await CarShare.find(CarShare.user_id == user_id).delete()
    await Notification.find(Notification.user_id == user_id).delete()
    await UserPreferences.find(UserPreferences.user_id == user_id).delete()
    await user.delete()
