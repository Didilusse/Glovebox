import os

import pytest
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient
from pymongo import MongoClient

import backend.database as database_module
from backend.config import settings
from backend.main import app


@pytest.fixture()
def api_client(monkeypatch):
    if os.getenv("USE_REAL_MONGODB") != "true":
        mock_client = AsyncMongoMockClient()
        monkeypatch.setattr(database_module, "client_factory", lambda _: mock_client)
        with TestClient(app) as client:
            yield client
        return

    uri = os.getenv("MONGODB_URI", settings.mongodb_uri)
    mongo_client = MongoClient(uri, serverSelectionTimeoutMS=500)
    mongo_client.admin.command("ping")

    test_database_name = os.getenv("TEST_DATABASE_NAME", f"{settings.database_name}_test")
    monkeypatch.setattr(settings, "database_name", test_database_name)
    database = mongo_client[test_database_name]
    database.cars.delete_many({})
    database.maintenance_logs.delete_many({})
    database.mods.delete_many({})
    database.schema_migrations.delete_many({})

    with TestClient(app) as client:
        yield client

    database.cars.delete_many({})
    database.maintenance_logs.delete_many({})
    database.mods.delete_many({})
    database.schema_migrations.delete_many({})
    mongo_client.close()
