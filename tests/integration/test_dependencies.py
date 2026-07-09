import pytest

from tests.integration.utils import assert_status, encode_urlencoded

pytestmark = pytest.mark.integration


def test_dependency_with_query_params(client):
    resp = client.get("/di-query", query=[("page", "3"), ("per_page", "50")])
    assert_status(resp, 200)
    assert resp.json() == {"page": 3, "per_page": 50}


def test_dependency_query_defaults(client):
    resp = client.get("/di-query")
    assert_status(resp, 200)
    assert resp.json() == {"page": 1, "per_page": 10}


def test_nested_dependency(client):
    resp = client.get("/di-nested", query=[("page", "2")])
    assert_status(resp, 200)
    assert resp.json() == {"wrapped": {"page": 2, "per_page": 10}}


def test_dependency_with_form_param(client):
    # Form() inside a dependency must trigger form extraction (profile
    # walks dependencies transitively)
    body, content_type = encode_urlencoded([("csrf", "tok-123")])
    resp = client.post("/di-form", content=body, content_type=content_type)
    assert_status(resp, 200)
    assert resp.json() == {"csrf": "tok-123"}


def test_dependency_with_form_param_missing_yields_422(client):
    body, content_type = encode_urlencoded([("other", "x")])
    resp = client.post("/di-form", content=body, content_type=content_type)
    assert_status(resp, 422)


def test_dependency_with_cookie_param(client):
    resp = client.get("/di-cookie", cookies={"session": "sess-9"})
    assert_status(resp, 200)
    assert resp.json() == {"session": "sess-9"}


def test_generator_dependency(client):
    resp = client.get("/di-generator")
    assert_status(resp, 200)
    assert resp.json() == {"value": "gen-value"}


def test_yield_dependency_open_during_endpoint(client):
    # The yielded resource is closed only after the endpoint finishes
    resp = client.get("/di-yield-open")
    assert_status(resp, 200)
    assert resp.json() == {"open": True}


def test_security_scopes_are_per_declaration(client):
    # Same dependency with different scopes must not share a cached result
    resp = client.get("/di-scopes")
    assert_status(resp, 200)
    assert resp.json() == {"read": ["read"], "admin": ["admin"]}


def test_dependency_with_bare_model_uses_query_on_get(client):
    resp = client.get("/di-model-query", query=[("term", "abc"), ("limit", "3")])
    assert_status(resp, 200)
    assert resp.json() == {"term": "abc", "limit": 3}


def test_security_dependency_authorized(client):
    resp = client.get("/secure", headers={"X-Api-Key": "secret-key"})
    assert_status(resp, 200)
    assert resp.json() == {"authorized": True}


def test_security_dependency_rejected(client):
    resp = client.get("/secure", headers={"X-Api-Key": "wrong"})
    assert_status(resp, 401)
    assert resp.json()["error"]["message"] == "Invalid API key"


def test_security_dependency_missing_header(client):
    resp = client.get("/secure")
    assert_status(resp, 401)
