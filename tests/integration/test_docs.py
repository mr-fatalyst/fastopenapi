import pytest

from tests.integration.utils import assert_status

pytestmark = pytest.mark.integration


def test_openapi_json_served(client):
    resp = client.get("/openapi.json")
    assert_status(resp, 200)
    schema = resp.json()
    assert schema["openapi"].startswith("3.")
    assert "/ping" in schema["paths"]
    assert "ErrorSchema" in schema["components"]["schemas"]


def test_swagger_ui_served(client):
    resp = client.get("/docs")
    assert_status(resp, 200)
    assert resp.headers["content-type"].startswith("text/html")
    assert b"swagger" in resp.body.lower()


def test_redoc_ui_served(client):
    resp = client.get("/redoc")
    assert_status(resp, 200)
    assert resp.headers["content-type"].startswith("text/html")
    assert b"redoc" in resp.body.lower()
