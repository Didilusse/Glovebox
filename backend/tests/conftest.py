import os

import pytest
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient
from pymongo import MongoClient

import backend.database as database_module
from backend.config import settings
from backend.main import app

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "correct-horse-battery"


@pytest.fixture(autouse=True)
def clear_login_limits():
    from backend.auth import login_buckets
    login_buckets.clear()
    yield
    login_buckets.clear()


@pytest.fixture(autouse=True)
def isolate_setup_token(monkeypatch):
    monkeypatch.setattr(settings, "setup_token", None)
    monkeypatch.setattr(settings, "reminder_worker_enabled", False)


class AuthTestClient(TestClient):
    """TestClient that attaches the logged-in user's Authorization header to every request.

    The api_client fixture registers the admin and stores the token here. Tests acting
    as a different user pass explicit headers=, which take precedence over the default.
    """

    default_headers: dict = {}

    def request(self, *args, **kwargs):
        headers = dict(self.default_headers)
        explicit = kwargs.pop("headers", None)
        if explicit:
            headers.update(explicit)
        return super().request(*args, headers=headers or None, **kwargs)


def setup_admin(client):
    """Run first-time setup on an empty database and store the admin token on the client."""
    response = client.post(
        "/auth/setup",
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    client.default_headers = {"Authorization": f"Bearer {payload['token']}"}
    return payload


def create_user(client, username, password="password123"):
    response = client.post("/users/", json={"username": username, "password": password})
    assert response.status_code == 201, response.text
    return response.json()


def auth_headers_for(client, username, password):
    """Log in as an existing user and return headers for acting as that user."""
    response = client.post(
        "/auth/login",
        json={"username": username, "password": password},
        headers={},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['token']}"}


def _wipe(database):
    database.cars.delete_many({})
    database.car_shares.delete_many({})
    database.maintenance_logs.delete_many({})
    database.mods.delete_many({})
    database.users.delete_many({})
    database.sessions.delete_many({})
    database.schema_migrations.delete_many({})
    database.user_preferences.delete_many({})
    database.notifications.delete_many({})


@pytest.fixture()
def raw_client(monkeypatch):
    """Unauthenticated client on an empty database — for testing the setup flow itself."""
    if os.getenv("USE_REAL_MONGODB") != "true":
        mock_client = AsyncMongoMockClient()
        monkeypatch.setattr(database_module, "client_factory", lambda _: mock_client)
        with AuthTestClient(app) as client:
            yield client
        return

    uri = os.getenv("MONGODB_URI", settings.mongodb_uri)
    mongo_client = MongoClient(uri, serverSelectionTimeoutMS=500)
    mongo_client.admin.command("ping")

    test_database_name = os.getenv("TEST_DATABASE_NAME", f"{settings.database_name}_test")
    monkeypatch.setattr(settings, "database_name", test_database_name)
    database = mongo_client[test_database_name]
    _wipe(database)

    with AuthTestClient(app) as client:
        yield client

    _wipe(database)
    mongo_client.close()


@pytest.fixture()
def api_client(monkeypatch):
    if os.getenv("USE_REAL_MONGODB") != "true":
        mock_client = AsyncMongoMockClient()
        monkeypatch.setattr(database_module, "client_factory", lambda _: mock_client)
        with AuthTestClient(app) as client:
            setup_admin(client)
            yield client
        return

    uri = os.getenv("MONGODB_URI", settings.mongodb_uri)
    mongo_client = MongoClient(uri, serverSelectionTimeoutMS=500)
    mongo_client.admin.command("ping")

    test_database_name = os.getenv("TEST_DATABASE_NAME", f"{settings.database_name}_test")
    monkeypatch.setattr(settings, "database_name", test_database_name)
    database = mongo_client[test_database_name]
    _wipe(database)

    with AuthTestClient(app) as client:
        setup_admin(client)
        yield client

    _wipe(database)
    mongo_client.close()
