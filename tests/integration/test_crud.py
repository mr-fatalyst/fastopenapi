import pytest

from tests.integration.utils import assert_status

pytestmark = pytest.mark.integration


def test_path_param_is_typed(client):
    resp = client.get("/items/42")
    assert_status(resp, 200)
    assert resp.json() == {"id": 42, "type": "int"}


def test_path_param_type_mismatch_yields_client_error(client):
    resp = client.get("/items/not-a-number")
    # Frameworks with typed converters answer 404, ours validates -> 422;
    # either way it must be a client error, not a 500
    assert 400 <= resp.status < 500, resp.status


def test_create_with_status_code_and_response_model(client):
    resp = client.post("/items", json_body={"name": "Widget", "price": 2.5})
    assert_status(resp, 201)
    assert resp.json() == {"id": 1, "name": "Widget"}


def test_put_with_path_and_body(client):
    resp = client.put("/items/7", json_body={"name": "Renamed"})
    assert_status(resp, 200)
    assert resp.json() == {"id": 7, "name": "Renamed"}


def test_patch_with_path_and_body(client):
    resp = client.patch("/items/7", json_body={"name": "Patched"})
    assert_status(resp, 200)
    assert resp.json() == {"id": 7, "patched": "Patched"}


def test_response_model_list(client):
    resp = client.get("/items-list")
    assert_status(resp, 200)
    assert resp.json() == [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]


def test_response_model_violation_yields_500(client):
    resp = client.get("/bad-response")
    assert_status(resp, 500)
    assert resp.json()["error"]["message"] == "Incorrect response type"


def test_multiple_path_params(client):
    resp = client.get("/things/tools/7")
    assert_status(resp, 200)
    assert resp.json() == {"category": "tools", "thing_id": 7}


def test_explicit_options_route(client):
    resp = client.options("/opts")
    assert_status(resp, 204)
    assert "GET" in resp.headers.get("allow", "")


def test_missing_required_query_yields_422(client):
    resp = client.get("/query-required")
    assert_status(resp, 422)


def test_unknown_path_yields_404(client):
    resp = client.get("/definitely-not-registered")
    assert_status(resp, 404)


def test_wrong_method_yields_405(client):
    resp = client.post("/ping", json_body={})
    assert_status(resp, 405)
