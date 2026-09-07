import re
from typing import Any, Optional
from urllib.parse import quote

import httpx


VPIC_DECODE_URL = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}"
RATINGS_SEARCH_URL = (
    "https://api.nhtsa.gov/SafetyRatings/modelyear/{year}/make/{make}/model/{model}"
)
RATINGS_DETAIL_URL = "https://api.nhtsa.gov/SafetyRatings/VehicleId/{vehicle_id}"
RECALLS_URL = "https://api.nhtsa.gov/recalls/recallsByVehicle"
NHTSA_VIN_LOOKUP_URL = "https://www.nhtsa.gov/recalls?vymm={vin}"


class NhtsaError(Exception):
    pass


def _headers() -> dict[str, str]:
    return {"User-Agent": "glovebox"}


def _campaign_number(value: Any) -> Any:
    if isinstance(value, str) and value.endswith("000"):
        return value[:-3]
    return value


def _manufacturer_recall_number(item: dict[str, Any]) -> Optional[str]:
    value = item.get("MfrRecallNumber") or item.get("ManufacturerRecallNumber")
    if value:
        return str(value)

    remedy = item.get("Remedy") or ""
    match = re.search(
        r"numbers? for this recall (?:is|are)\s+(?:[A-Za-z]+:\s*)?([A-Z0-9-]+)",
        remedy,
        re.IGNORECASE,
    )
    return match.group(1) if match else None


async def decode_vin(vin: str) -> dict[str, Any]:
    """Decode a VIN using NHTSA's free VPIC service."""
    url = VPIC_DECODE_URL.format(vin=vin)
    async with httpx.AsyncClient(timeout=15, headers=_headers()) as client:
        response = await client.get(url, params={"format": "json"})
        response.raise_for_status()
        payload = response.json()

    results = payload.get("Results", []) or []
    fields: dict[str, Any] = {}
    raw: list[dict[str, Any]] = []
    for item in results:
        value = item.get("Value")
        variable = item.get("Variable")
        if variable:
            fields[variable] = value
        raw.append(
            {"variable": variable, "value": value, "value_id": item.get("ValueId")}
        )

    return {
        "message": payload.get("Message"),
        "fields": fields,
        "raw": raw,
        "make": fields.get("Make"),
        "model": fields.get("Model"),
        "year": fields.get("Model Year"),
    }


async def get_safety_ratings(
    year: str | int, make: str, model: str
) -> dict[str, Any]:
    """Look up NHTSA crash-test safety ratings for a make/model/year."""
    make_clean = make.replace(" ", "%20").replace("/", "%2F")
    model_clean = model.replace(" ", "%20").replace("/", "%2F")
    url = RATINGS_SEARCH_URL.format(year=year, make=make_clean, model=model_clean)

    async with httpx.AsyncClient(timeout=15, headers=_headers()) as client:
        search_response = await client.get(url, params={"format": "json"})
        search_response.raise_for_status()
        search_payload = search_response.json()

    vehicles = search_payload.get("Results", []) or []
    vehicle_id = vehicles[0]["VehicleId"] if vehicles else None

    detail = None
    if vehicle_id is not None:
        detail_url = RATINGS_DETAIL_URL.format(vehicle_id=vehicle_id)
        async with httpx.AsyncClient(timeout=15, headers=_headers()) as client:
            detail_response = await client.get(detail_url, params={"format": "json"})
            if detail_response.status_code == 200:
                detail_results = detail_response.json().get("Results", []) or []
                detail = detail_results[0] if detail_results else None

    return {
        "vehicles": vehicles,
        "selected": detail,
    }


async def get_recalls(year: str | int, make: str, model: str) -> list[dict[str, Any]]:
    """Fetch safety recalls for a make/model/year via NHTSA's public API."""
    models = [model]
    base_model = model.split()[0]
    if base_model.lower() != model.lower():
        models.append(base_model)

    results: list[dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=15, headers=_headers()) as client:
        for recall_model in models:
            # NHTSA rejects '+' for spaces, so encode query values with '%20'.
            url = (
                f"{RECALLS_URL}?make={quote(make, safe='')}&model={quote(recall_model, safe='')}"
                f"&modelYear={quote(str(year), safe='')}"
            )
            response = await client.get(url)
            payload = response.json()
            # This endpoint returns a valid empty payload with HTTP 400 when an
            # exact model variant is not in its recall database.
            if response.status_code >= 400 and "results" not in payload:
                response.raise_for_status()
            results = payload.get("results", []) or []
            if results:
                break

    recalls: list[dict[str, Any]] = []
    for item in results:
        campaign_number = item.get("NHTSACampaignNumber")
        recalls.append(
            {
                "recall_number": _campaign_number(campaign_number),
                "nhtsa_campaign_number": campaign_number,
                "manufacturer_recall_number": _manufacturer_recall_number(item),
                "nhtsa_action_number": item.get("NHTSAActionNumber"),
                "manufacturer": item.get("Manufacturer"),
                "component": item.get("Component"),
                "summary": item.get("Summary"),
                "consequence": item.get("Consequence"),
                "remedy": item.get("Remedy"),
                "notes": item.get("Notes"),
                "report_date": item.get("ReportReceivedDate"),
                "park_it": item.get("parkIt"),
                "park_outside": item.get("parkOutSide"),
                "status": item.get("RecallStatus") or item.get("recallStatus"),
                "raw": item,
            }
        )
    return recalls


async def get_nhtsa_data(car: Any) -> dict[str, Any]:
    """Pull all available NHTSA information for a car into a single payload."""
    vin = getattr(car, "vin", None)
    if not vin:
        raise NhtsaError("VIN is required to look up NHTSA information")

    errors: dict[str, str] = {}
    decode: Optional[dict[str, Any]] = None
    ratings: Optional[dict[str, Any]] = None
    recalls: list[dict[str, Any]] = []

    try:
        decode = await decode_vin(vin)
    except Exception as exc:  # noqa: BLE001 - collect and surface in response
        errors["decode"] = str(exc)

    recall_year = decode.get("year") if decode else None
    recall_make = decode.get("make") if decode else None
    recall_model = decode.get("model") if decode else None

    try:
        ratings = await get_safety_ratings(car.year, car.make, car.model)
    except Exception as exc:  # noqa: BLE001
        errors["ratings"] = str(exc)

    try:
        recalls = await get_recalls(
            recall_year or car.year,
            recall_make or car.make,
            recall_model or car.model,
        )
    except Exception as exc:  # noqa: BLE001
        errors["recalls"] = str(exc)

    return {
        "vin": vin,
        "decode": decode,
        "ratings": ratings,
        "recalls": recalls,
        "recall_lookup_url": NHTSA_VIN_LOOKUP_URL.format(vin=vin),
        "errors": errors,
    }
