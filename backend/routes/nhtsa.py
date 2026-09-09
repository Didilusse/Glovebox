from fastapi import APIRouter, Depends, HTTPException

from backend.auth import get_current_user, get_vehicle_car
from backend.models.car_model import CarModel, validate_vin
from backend.models.user import User
from backend.services.nhtsa import NhtsaError, decode_vin, get_nhtsa_data


router = APIRouter(tags=["NHTSA"])


@router.get("/nhtsa/decode/{vin}")
async def decode_vehicle_vin(vin: str, _: User = Depends(get_current_user)):
    try:
        vin = validate_vin(vin)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return await decode_vin(vin)


@router.get("/cars/{car_id}/nhtsa/")
async def get_car_nhtsa(car: CarModel = Depends(get_vehicle_car)):
    try:
        return await get_nhtsa_data(car)
    except NhtsaError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
