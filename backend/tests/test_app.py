import importlib
main = importlib.import_module("backend.main")


def test_docs_endpoints_disabled_by_default():
    from fastapi.testclient import TestClient

    client = TestClient(main.app)
    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404
    assert client.get("/openapi.json").status_code == 404
