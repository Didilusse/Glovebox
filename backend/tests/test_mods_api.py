from backend.tests.test_api import create_car


def create_mod(client, car_id, name, status="planned"):
    response = client.post(
        f"/cars/{car_id}/planned-mods/",
        json={
            "name": name,
            "type": "modification",
            "category": "engine",
            "status": status,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def list_mods(client, car_id):
    response = client.get(f"/cars/{car_id}/planned-mods/")
    assert response.status_code == 200, response.text
    return response.json()


def column(mods, status):
    return [(mod["name"], mod["position"]) for mod in mods if mod["status"] == status]


def test_mods_append_and_list_in_status_position_id_order(api_client):
    car = create_car(api_client)
    planned_a = create_mod(api_client, car["_id"], "Planned A")
    create_mod(api_client, car["_id"], "Purchased A", "purchased")
    planned_b = create_mod(api_client, car["_id"], "Planned B")
    create_mod(api_client, car["_id"], "Installed A", "installed")

    assert planned_a["position"] == 0
    assert planned_b["position"] == 1
    mods = list_mods(api_client, car["_id"])
    assert [(mod["status"], mod["position"], mod["_id"]) for mod in mods] == sorted(
        (mod["status"], mod["position"], mod["_id"]) for mod in mods
    )
    assert column(mods, "planned") == [("Planned A", 0), ("Planned B", 1)]


def test_move_reorders_same_column_and_renumbers(api_client):
    car = create_car(api_client)
    first = create_mod(api_client, car["_id"], "First")
    create_mod(api_client, car["_id"], "Second")
    create_mod(api_client, car["_id"], "Third")

    response = api_client.patch(
        f"/cars/{car['_id']}/planned-mods/{first['_id']}/move",
        json={"status": "planned", "position": 2},
    )
    assert response.status_code == 200, response.text
    assert response.json()["position"] == 2
    assert column(list_mods(api_client, car["_id"]), "planned") == [
        ("Second", 0),
        ("Third", 1),
        ("First", 2),
    ]


def test_cross_column_move_renumbers_both_columns(api_client):
    car = create_car(api_client)
    create_mod(api_client, car["_id"], "Planned A")
    moving = create_mod(api_client, car["_id"], "Planned B")
    create_mod(api_client, car["_id"], "Planned C")
    create_mod(api_client, car["_id"], "Purchased A", "purchased")
    create_mod(api_client, car["_id"], "Purchased B", "purchased")

    response = api_client.patch(
        f"/cars/{car['_id']}/planned-mods/{moving['_id']}/move",
        json={"status": "purchased", "position": 1},
    )
    assert response.status_code == 200, response.text
    mods = list_mods(api_client, car["_id"])
    assert column(mods, "planned") == [("Planned A", 0), ("Planned C", 1)]
    assert column(mods, "purchased") == [
        ("Purchased A", 0),
        ("Planned B", 1),
        ("Purchased B", 2),
    ]


def test_generic_status_update_appends_to_destination(api_client):
    car = create_car(api_client)
    moving = create_mod(api_client, car["_id"], "Moving")
    create_mod(api_client, car["_id"], "Remaining")
    create_mod(api_client, car["_id"], "Purchased", "purchased")

    response = api_client.patch(
        f"/cars/{car['_id']}/planned-mods/{moving['_id']}",
        json={"status": "purchased"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["position"] == 1
    mods = list_mods(api_client, car["_id"])
    assert column(mods, "planned") == [("Remaining", 0)]
    assert column(mods, "purchased") == [("Purchased", 0), ("Moving", 1)]


def test_move_rejects_invalid_positions_and_cross_car_mods(api_client):
    car = create_car(api_client)
    other_car = create_car(api_client, license_plate="OTHER")
    mod = create_mod(api_client, car["_id"], "Part")
    url = f"/cars/{car['_id']}/planned-mods/{mod['_id']}/move"

    assert api_client.patch(url, json={"status": "planned", "position": -1}).status_code == 422
    assert api_client.patch(url, json={"status": "unknown", "position": 0}).status_code == 422
    assert api_client.patch(url, json={"status": "planned", "position": 2}).status_code == 422
    response = api_client.patch(
        f"/cars/{other_car['_id']}/planned-mods/{mod['_id']}/move",
        json={"status": "planned", "position": 0},
    )
    assert response.status_code == 404
    assert column(list_mods(api_client, car["_id"]), "planned") == [("Part", 0)]


def test_create_mod_serializes_planning_fields_and_defaults(api_client):
    car = create_car(api_client)
    response = api_client.post(
        f"/cars/{car['_id']}/planned-mods/",
        json={
            "name": "Brake kit",
            "type": "modification",
            "category": "brakes",
            "priority": "high",
            "install_method": "shop",
            "part_number": "  BBK-100  ",
            "target_date": "2026-10-15",
        },
    )

    assert response.status_code == 201, response.text
    created = response.json()
    assert created["priority"] == "high"
    assert created["install_method"] == "shop"
    assert created["part_number"] == "BBK-100"
    assert created["target_date"] == "2026-10-15"

    defaulted = create_mod(api_client, car["_id"], "Defaulted")
    assert defaulted["priority"] == "medium"
    assert defaulted["install_method"] == "undecided"
    assert defaulted["part_number"] is None
    assert defaulted["target_date"] is None


def test_update_mod_planning_fields_and_clear_optional_values(api_client):
    car = create_car(api_client)
    mod = create_mod(api_client, car["_id"], "Part")
    url = f"/cars/{car['_id']}/planned-mods/{mod['_id']}"

    response = api_client.patch(
        url,
        json={
            "priority": "low",
            "install_method": "diy",
            "part_number": "PART-42",
            "target_date": "2026-11-01",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["priority"] == "low"
    assert response.json()["install_method"] == "diy"
    assert response.json()["part_number"] == "PART-42"
    assert response.json()["target_date"] == "2026-11-01"

    cleared = api_client.patch(url, json={"part_number": None, "target_date": None})
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["part_number"] is None
    assert cleared.json()["target_date"] is None


def test_mod_api_rejects_invalid_and_unknown_planning_fields(api_client):
    car = create_car(api_client)
    base_url = f"/cars/{car['_id']}/planned-mods/"
    payload = {
        "name": "Part",
        "type": "modification",
        "category": "engine",
    }

    assert api_client.post(base_url, json=payload | {"priority": "urgent"}).status_code == 422
    assert api_client.post(base_url, json=payload | {"part_number": " "}).status_code == 422
    assert api_client.post(base_url, json=payload | {"unknown": True}).status_code == 422

    mod = create_mod(api_client, car["_id"], "Existing")
    update_url = f"{base_url}{mod['_id']}"
    assert api_client.patch(update_url, json={"unknown": True}).status_code == 422
