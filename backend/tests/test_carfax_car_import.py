from backend.models.car_model import CarModel
from backend.tests.test_carfax_importer import sample_carfax_pages


def _preview(client, monkeypatch):
    monkeypatch.setattr(
        "backend.routes.maintenance_import.extract_pdf_pages",
        lambda _: sample_carfax_pages(),
    )
    return client.post(
        "/cars/import/carfax/preview",
        files={"file": ("carfax.pdf", b"%PDF-test", "application/pdf")},
    )


def _records(preview):
    allowed = {
        "date_of_service", "mileage", "cost", "done_by", "work_done", "category",
        "notes", "service_provider", "source_record_key",
    }
    return [{key: value for key, value in record.items() if key in allowed} for record in preview["records"]]


def test_carfax_creates_car_and_complete_history(api_client, monkeypatch):
    response = _preview(api_client, monkeypatch)
    assert response.status_code == 200, response.text
    preview = response.json()
    assert preview["report"].items() >= {
        "vin": "1HGCP3F89BA028384",
        "year": 2011,
        "make": "Honda",
        "model": "ACCORD EX-L V6",
    }.items()
    assert preview["summary"]["found"] == 29
    assert preview["summary"]["latest_mileage"] == 108707

    response = api_client.post(
        "/cars/import/carfax/confirm",
        json={
            "report_vin": preview["report"]["vin"],
            "vehicle": {
                "year": preview["report"]["year"],
                "make": preview["report"]["make"],
                "model": preview["report"]["model"],
                "vin": preview["report"]["vin"],
                "mileage": preview["summary"]["latest_mileage"],
                "fuel_type": "gas",
            },
            "records": _records(preview),
        },
    )
    assert response.status_code == 201, response.text
    result = response.json()
    assert result["created"] == 29
    assert result["car"]["vin"] == "1HGCP3F89BA028384"
    assert result["car"]["mileage"] == 108707
    assert len(api_client.get(f"/cars/{result['car']['_id']}/logs/").json()) == 29

    assert _preview(api_client, monkeypatch).status_code == 409


def test_failed_history_import_removes_new_car(api_client, monkeypatch):
    preview = _preview(api_client, monkeypatch).json()

    async def fail_import(*_args, **_kwargs):
        raise RuntimeError("database failure")

    monkeypatch.setattr("backend.routes.carfax_car_import.create_imported_logs", fail_import)
    try:
        api_client.post(
            "/cars/import/carfax/confirm",
            json={
                "report_vin": preview["report"]["vin"],
                "vehicle": {
                    "year": 2011, "make": "Honda", "model": "Accord",
                    "vin": preview["report"]["vin"], "mileage": 108707,
                },
                "records": _records(preview),
            },
        )
    except RuntimeError:
        pass

    async def car_count():
        return await CarModel.find_all().count()

    assert api_client.portal.call(car_count) == 0
