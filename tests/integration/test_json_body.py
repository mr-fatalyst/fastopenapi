import pytest

from tests.integration.utils import assert_status

pytestmark = pytest.mark.integration


def test_json_object(client):
    resp = client.post("/json-echo", json_body={"name": "x", "price": 2.5})
    assert_status(resp, 200)
    assert resp.json() == {"name": "x", "price": 2.5}


def test_json_with_charset_in_content_type(client):
    resp = client.post(
        "/json-echo",
        content=b'{"name": "x", "price": 2.5}',
        content_type="application/json; charset=utf-8",
    )
    assert_status(resp, 200)
    assert resp.json() == {"name": "x", "price": 2.5}


def test_malformed_json_yields_422_with_json_error(client):
    resp = client.post(
        "/json-echo", content=b'{"name": broken', content_type="application/json"
    )
    assert_status(resp, 422)
    assert "json" in resp.text.lower()


def test_array_body_for_object_param_yields_422(client):
    resp = client.post("/json-echo", json_body=[{"name": "x"}])
    assert_status(resp, 422)


def test_wrong_field_types_yield_422(client):
    resp = client.post("/json-echo", json_body={"name": "x", "price": "not-a-number"})
    assert_status(resp, 422)
    assert "error" in resp.json()


def test_missing_required_field_yields_422(client):
    resp = client.post("/json-echo", json_body={"price": 1.5})
    assert_status(resp, 422)
