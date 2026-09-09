from backend.tests.test_api import create_car
from backend.tests.test_carfax_importer import sample_carfax_pages


def _preview(client, car_id, monkeypatch):
    monkeypatch.setattr(
        "backend.routes.maintenance_import.extract_pdf_pages",
        lambda _: sample_carfax_pages(),
    )
    return client.post(
        f"/cars/{car_id}/logs/import/preview",
        files={"file": ("carfax.pdf", b"%PDF-test", "application/pdf")},
    )


def _confirm_payload(preview):
    allowed = {
        "date_of_service",
        "mileage",
        "cost",
        "done_by",
        "work_done",
        "category",
        "notes",
        "service_provider",
        "source_record_key",
    }
    return {
        "report_vin": preview["report"]["vin"],
        "records": [
            {key: value for key, value in record.items() if key in allowed}
            for record in preview["records"]
            if not record["duplicate"]
        ],
    }


def test_preview_and_idempotent_confirm(api_client, monkeypatch):
    car = create_car(api_client, vin="1HGCP3F89BA028384")
    response = _preview(api_client, car["_id"], monkeypatch)
    assert response.status_code == 200, response.text
    preview = response.json()
    assert preview["summary"] == {
        "found": 29,
        "new": 29,
        "duplicates": 0,
        "missing_mileage": 10,
    }
    assert api_client.get(f"/cars/{car['_id']}/logs/").json() == []

    payload = _confirm_payload(preview)
    response = api_client.post(f"/cars/{car['_id']}/logs/import/confirm", json=payload)
    assert response.status_code == 201, response.text
    assert response.json()["created"] == 29
    assert api_client.get(f"/cars/{car['_id']}").json()["mileage"] == 108707
    stats = api_client.get(f"/cars/{car['_id']}/stats/").json()
    assert stats["total_spent"] == 0
    assert stats["avg_cost_per_service"] == 0

    response = api_client.post(f"/cars/{car['_id']}/logs/import/confirm", json=payload)
    assert response.status_code == 201, response.text
    assert response.json()["created"] == 0
    assert response.json()["skipped_duplicates"] == 29


def test_preview_rejects_vin_mismatch_and_invalid_files(api_client, monkeypatch):
    car = create_car(api_client, vin="JHGCP3F89BA028384")
    response = _preview(api_client, car["_id"], monkeypatch)
    assert response.status_code == 409

    response = api_client.post(
        f"/cars/{car['_id']}/logs/import/preview",
        files={"file": ("carfax.txt", b"not a pdf", "text/plain")},
    )
    assert response.status_code == 415
