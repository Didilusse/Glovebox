from fastapi import APIRouter, Depends, HTTPException

from backend.auth import get_vehicle_car
from backend.models.car_model import CarModel
from backend.services.nhtsa import NhtsaError, get_nhtsa_data


router = APIRouter(prefix="/cars/{car_id}/nhtsa", tags=["NHTSA"])


@router.get("/")
async def get_car_nhtsa(car: CarModel = Depends(get_vehicle_car)):
    try:
        return await get_nhtsa_data(car)
    except NhtsaError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
