import asyncio
import importlib

import backend.database as database


async def _noop():
    return None


# Patch init_db to avoid requiring a real MongoDB in tests
database.init_db = _noop

# Reload main so the patched init_db is used in the lifespan
main = importlib.import_module("backend.main")


def test_docs_endpoint_available():
    from fastapi.testclient import TestClient

    client = TestClient(main.app)
    res = client.get("/docs")
    assert res.status_code in (200, 307, 308)
