import pytest

from tests.integration.utils import assert_status

pytestmark = pytest.mark.integration


def test_list_of_models_with_body_marker(client):
    resp = client.post("/json-list", json_body=[{"name": "a"}, {"name": "b"}])
    assert_status(resp, 200)
    assert resp.json() == {"names": ["a", "b"]}


def test_list_of_models_without_body_marker(client):
    resp = client.post("/json-list-plain", json_body=[{"name": "a"}, {"name": "b"}])
    assert_status(resp, 200)
    assert resp.json() == {"names": ["a", "b"]}


def test_optional_model_receives_body(client):
    resp = client.post("/json-optional", json_body={"name": "opt"})
    assert_status(resp, 200)
    assert resp.json() == {"received": "opt"}


def test_optional_model_defaults_to_none_without_body(client):
    resp = client.post("/json-optional")
    assert_status(resp, 200)
    assert resp.json() == {"received": None}


def test_delete_reads_json_body(client):
    resp = client.delete("/items", json_body={"ids": [1, 2]})
    assert_status(resp, 200)
    assert resp.json() == {"ids": [1, 2]}


def test_annotated_query_alias(client):
    resp = client.get("/annotated", query=[("q-alias", "hello")])
    assert_status(resp, 200)
    assert resp.json() == {"q": "hello", "limit": 1}


def test_annotated_query_constraint(client):
    resp = client.get("/annotated", query=[("limit", "0")])
    assert_status(resp, 422)


def test_get_model_maps_to_query_params(client):
    resp = client.get("/search", query=[("term", "abc"), ("limit", "5")])
    assert_status(resp, 200)
    assert resp.json() == {"term": "abc", "limit": 5}


def test_get_model_missing_required_query_yields_422(client):
    resp = client.get("/search")
    assert_status(resp, 422)


def test_list_body_with_invalid_element_yields_422(client):
    # plain (marker-less) container goes through TypeAdapter validation
    resp = client.post("/json-list-plain", json_body=[{"name": "ok"}, {"price": 2}])
    assert_status(resp, 422)


def test_two_body_params_are_embedded_by_name(client):
    resp = client.post("/embedded", json_body={"a": 5})
    assert_status(resp, 200)
    assert resp.json() == {"a": 5, "b": "default-b"}
