from datetime import date
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict, Field, field_validator
from starlette.concurrency import run_in_threadpool

from backend.auth import get_maintenance_car
from backend.models.car_model import CarModel
from backend.models.maintenance_log import Category, DoneBy, MaintenanceLog
from backend.services.carfax_importer import (
    CarfaxParseError,
    extract_pdf_pages,
    make_source_record_key,
    parse_carfax_pages,
)
from backend.services.maintenance import create_imported_logs


MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_IMPORT_RECORDS = 100
MAX_WORK_DONE_LENGTH = 500
MAX_NOTES_LENGTH = 5000
router = APIRouter(prefix="/cars/{car_id}/logs/import", tags=["Maintenance Import"])


async def get_import_car(car: CarModel = Depends(get_maintenance_car)) -> CarModel:
    if car.is_deleting:
        raise HTTPException(status_code=404, detail="Car not found")
    return car


class ImportRecord(BaseModel):
    date_of_service: date
    mileage: int | None = Field(None, ge=0, strict=True)
    cost: float | None = Field(None, ge=0, allow_inf_nan=False)
    done_by: DoneBy = DoneBy.shop
    work_done: str = Field(min_length=1, max_length=500)
    category: Category = Category.other
    notes: str | None = Field(None, max_length=5000)
    service_provider: str | None = Field(None, max_length=200)
    source_record_key: str = Field(min_length=64, max_length=64)

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("source_record_key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        if any(character not in "0123456789abcdef" for character in value):
            raise ValueError("source_record_key must be a SHA-256 hex digest")
        return value


class ConfirmImportRequest(BaseModel):
    report_vin: str = Field(min_length=17, max_length=17)
    records: list[ImportRecord] = Field(min_length=1, max_length=MAX_IMPORT_RECORDS)

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


@router.post("/preview")
async def preview_carfax_import(
    file: UploadFile = File(...),
    car: CarModel = Depends(get_import_car),
):
    report = await parse_uploaded_carfax(file)

    _validate_vin(car.vin, report.vin)
    keys = [
        make_source_record_key(
            report.vin,
            record.date_of_service,
            record.mileage,
            record.service_provider,
            _prepare_work_description(record.work_done)[0],
        )
        for record in report.records
    ]
    existing = await MaintenanceLog.find(
        {"car_id": car.id, "source": "carfax", "source_record_key": {"$in": keys}}
    ).to_list()
    existing_keys = {log.source_record_key for log in existing}

    records = serialize_import_records(report, existing_keys)
    duplicates = sum(record["duplicate"] for record in records)
    warnings = list(report.warnings)
    if not car.vin:
        warnings.append("This vehicle has no VIN saved; verify the report VIN before importing")
    return {
        "report": serialize_report_vehicle(report),
        "records": records,
        "warnings": warnings,
        "summary": {
            "found": len(records),
            "new": len(records) - duplicates,
            "duplicates": duplicates,
            "missing_mileage": sum(record["mileage"] is None for record in records),
        },
    }


async def parse_uploaded_carfax(file: UploadFile):
    filename = file.filename or ""
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="Only PDF files are supported")
    if file.content_type not in {"application/pdf", "application/x-pdf"}:
        raise HTTPException(status_code=415, detail="Only PDF files are supported")

    contents = await file.read(MAX_UPLOAD_BYTES + 1)
    await file.close()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="PDF exceeds the 10 MB limit")
    if not contents.startswith(b"%PDF-"):
        raise HTTPException(status_code=415, detail="The uploaded file is not a PDF")

    try:
        pages = await run_in_threadpool(extract_pdf_pages, contents)
        return await run_in_threadpool(parse_carfax_pages, pages)
    except CarfaxParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def serialize_import_records(report, existing_keys: set[str] | None = None):
    existing_keys = existing_keys or set()
    records = []
    for record in report.records:
        work_done, notes, description_warning = _prepare_work_description(record.work_done)
        key = make_source_record_key(
            report.vin,
            record.date_of_service,
            record.mileage,
            record.service_provider,
            work_done,
        )
        records.append(
            {
                "date_of_service": record.date_of_service,
                "mileage": record.mileage,
                "cost": None,
                "done_by": "shop",
                "work_done": work_done,
                "category": record.category,
                "notes": notes,
                "service_provider": record.service_provider,
                "source_record_key": key,
                "source_page": record.page,
                "warnings": record.warnings + ([description_warning] if description_warning else []),
                "duplicate": key in existing_keys,
            }
        )

    return records


def _prepare_work_description(work_done: str) -> tuple[str, str, str | None]:
    if len(work_done) <= MAX_WORK_DONE_LENGTH:
        return work_done, "Imported from CARFAX", None

    shortened = work_done[:MAX_WORK_DONE_LENGTH - 3].rsplit("; ", 1)[0].rstrip()
    if not shortened:
        shortened = work_done[:MAX_WORK_DONE_LENGTH - 3].rstrip()
    notes = f"Imported from CARFAX. Full work description: {work_done}"
    return (
        f"{shortened}...",
        notes[:MAX_NOTES_LENGTH],
        "Work description was shortened to fit the maintenance title; additional text is in notes",
    )


def serialize_report_vehicle(report):
    return {
        "vin": report.vin,
        "vehicle": report.vehicle,
        "year": report.year,
        "make": report.make,
        "model": report.model,
        "fuel_type": report.fuel_type,
    }


@router.post("/confirm", status_code=201)
async def confirm_carfax_import(payload: ConfirmImportRequest, car: CarModel = Depends(get_import_car)):
    report_vin = payload.report_vin.upper()
    _validate_vin(car.vin, report_vin)

    records: list[dict] = []
    seen_keys: set[str] = set()
    for submitted in payload.records:
        expected_key = make_source_record_key(
            report_vin,
            submitted.date_of_service,
            submitted.mileage,
            submitted.service_provider,
            submitted.work_done,
        )
        if expected_key in seen_keys:
            raise HTTPException(status_code=422, detail="The import contains duplicate records")
        seen_keys.add(expected_key)
        record = submitted.model_dump()
        record["source_record_key"] = expected_key
        records.append(record)

    created, skipped = await create_imported_logs(car.id, records)
    return {"created": len(created), "skipped_duplicates": skipped, "records": created}


def _validate_vin(car_vin: str | None, report_vin: str) -> None:
    if car_vin and car_vin.upper() != report_vin.upper():
        raise HTTPException(status_code=409, detail="The CARFAX VIN does not match this vehicle")
