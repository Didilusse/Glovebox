from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException

from backend.models.car_model import CarModel
from backend.services.nhtsa import NhtsaError, get_nhtsa_data


router = APIRouter(prefix="/cars/{car_id}/nhtsa", tags=["NHTSA"])


@router.get("/")
async def get_car_nhtsa(car_id: PydanticObjectId):
    car = await CarModel.get(car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    try:
        return await get_nhtsa_data(car)
    except NhtsaError as exc:
        raise HTTPException(status_code=422, detail=str(exc))