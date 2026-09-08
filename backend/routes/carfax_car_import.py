import re

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, ConfigDict, Field

from backend.auth import car_response, ensure_car_owner_active, get_current_user
from beanie import PydanticObjectId

from backend.models.car_model import CarCreate, CarModel
from backend.models.user import User
from backend.routes.maintenance_import import (
    ImportRecord,
    parse_uploaded_carfax,
    serialize_import_records,
    serialize_report_vehicle,
)
from backend.services.carfax_importer import make_source_record_key
from backend.services.maintenance import create_imported_logs
from backend.config import settings
from backend.services.quotas import QuotaExceeded, claim_quota, release_quota


router = APIRouter(prefix="/cars/import/carfax", tags=["Car Import"])


class CarfaxCarConfirmRequest(BaseModel):
    report_vin: str = Field(pattern=r"^[A-HJ-NPR-Z0-9]{17}$")
    vehicle: CarCreate
    records: list[ImportRecord] = Field(min_length=1, max_length=100)

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


@router.post("/preview")
async def preview_carfax_car(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    report = await parse_uploaded_carfax(file)
    await _reject_existing_vin(report.vin, user)
    records = serialize_import_records(report)
    return {
        "report": serialize_report_vehicle(report),
        "records": records,
        "warnings": report.warnings,
        "summary": {
            "found": len(records),
            "missing_mileage": sum(record["mileage"] is None for record in records),
            "latest_mileage": max(
                (record["mileage"] for record in records if record["mileage"] is not None),
                default=None,
            ),
        },
    }


@router.post("/confirm", status_code=201)
async def confirm_carfax_car(payload: CarfaxCarConfirmRequest, user: User = Depends(get_current_user)):
    report_vin = payload.report_vin.upper()
    if not payload.vehicle.vin or payload.vehicle.vin.upper() != report_vin:
        raise HTTPException(status_code=422, detail="The vehicle VIN must match the CARFAX report")
    await _reject_existing_vin(report_vin, user)

    records = []
    seen_keys: set[str] = set()
    for submitted in payload.records:
        key = make_source_record_key(
            report_vin,
            submitted.date_of_service,
            submitted.mileage,
            submitted.service_provider,
            submitted.work_done,
        )
        if key in seen_keys:
            raise HTTPException(status_code=422, detail="The import contains duplicate records")
        seen_keys.add(key)
        record = submitted.model_dump()
        record["source_record_key"] = key
        records.append(record)

    car_data = payload.vehicle.model_dump()
    car_data["vin"] = report_vin
    if car_data["initial_mileage"] is None and car_data["mileage"] is not None:
        car_data["initial_mileage"] = car_data["mileage"]
    car = CarModel(id=PydanticObjectId(), owner_id=user.id, **car_data)
    try:
        await claim_quota("cars", user.id, car.id, settings.max_cars_per_user,
                          CarModel.get_pymongo_collection(), {"owner_id": user.id})
    except QuotaExceeded:
        raise HTTPException(409, "Vehicle quota reached") from None
    try:
        await car.insert()
        await ensure_car_owner_active(car)
        created, skipped = await create_imported_logs(car.id, records)
    except Exception:
        await car.delete()
        await release_quota("cars", car.id)
        raise

    saved_car = await CarModel.get(car.id)
    return {"car": await car_response(saved_car, user), "created": len(created), "skipped_duplicates": skipped}


async def _reject_existing_vin(vin: str, user: User) -> None:
    escaped = re.escape(vin)
    existing = await CarModel.find_one({"owner_id": user.id, "vin": {"$regex": f"^{escaped}$", "$options": "i"}})
    if existing:
        raise HTTPException(status_code=409, detail="A vehicle with this VIN already exists")
