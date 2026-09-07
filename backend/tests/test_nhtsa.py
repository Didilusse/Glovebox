import asyncio

from backend.tests.test_api import create_car
from backend.services import nhtsa


def test_nhtsa_requires_vin(api_client, monkeypatch):
    car = create_car(api_client)
    response = api_client.get(f"/cars/{car['_id']}/nhtsa/")
    assert response.status_code == 422
    assert "VIN" in response.json()["detail"]


def test_nhtsa_returns_combined_payload(api_client, monkeypatch):
    car = create_car(api_client, vin="1HGCM82633A004352")

    async def fake_get_nhtsa_data(car):
        return {
            "vin": car.vin,
            "decode": {"make": "HONDA", "model": "Accord"},
            "ratings": {"vehicles": [{"VehicleId": 1}]},
            "recalls": [{"recall_number": "22V164000"}],
            "errors": {},
        }

    monkeypatch.setattr(
        "backend.routes.nhtsa.get_nhtsa_data",
        fake_get_nhtsa_data,
    )

    response = api_client.get(f"/cars/{car['_id']}/nhtsa/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["vin"] == "1HGCM82633A004352"
    assert payload["decode"]["make"] == "HONDA"
    assert payload["recalls"][0]["recall_number"] == "22V164000"


def test_nhtsa_not_found(api_client):
    response = api_client.get("/cars/64b000000000000000000000/nhtsa/")
    assert response.status_code == 404


def test_nhtsa_uses_vin_decoded_vehicle_for_recalls(monkeypatch):
    calls = []

    async def fake_decode_vin(vin):
        return {"make": "HONDA", "model": "Accord", "year": "2011"}

    async def fake_ratings(*_):
        return {"vehicles": [], "selected": None}

    async def fake_recalls(year, make, model):
        calls.append((year, make, model))
        return []

    monkeypatch.setattr(nhtsa, "decode_vin", fake_decode_vin)
    monkeypatch.setattr(nhtsa, "get_safety_ratings", fake_ratings)
    monkeypatch.setattr(nhtsa, "get_recalls", fake_recalls)

    car = type(
        "Car",
        (),
        {
            "vin": "1HGCP3F89BA028384",
            "year": 2011,
            "make": "Honda",
            "model": "ACCORD EX-L V6",
        },
    )()
    result = asyncio.run(nhtsa.get_nhtsa_data(car))

    assert result["errors"] == {}
    assert calls == [("2011", "HONDA", "Accord")]
    assert result["recall_lookup_url"] == "https://www.nhtsa.gov/recalls?vymm=1HGCP3F89BA028384"


def test_recall_fields_include_campaign_and_manufacturer_number():
    item = {
        "NHTSACampaignNumber": "24V110000",
        "Manufacturer": "Volkswagen Group of America, Inc.",
        "Remedy": "Volkswagen's numbers for this recall are VW: 20UF/Audi: 20YF.",
    }

    assert nhtsa._campaign_number(item["NHTSACampaignNumber"]) == "24V110"
    assert nhtsa._manufacturer_recall_number(item) == "20UF"
