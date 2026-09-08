import importlib
main = importlib.import_module("backend.main")


def test_docs_endpoint_available():
    from fastapi.testclient import TestClient

    client = TestClient(main.app)
    res = client.get("/docs")
    assert res.status_code in (200, 307, 308)
