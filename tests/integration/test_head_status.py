import pytest

from tests.integration.utils import assert_status

pytestmark = pytest.mark.integration


def test_head_on_get_route(client):
    # body handling for HEAD is transport-specific, so only the status matters
    resp = client.head("/head-me")
    assert_status(resp, 200)


def test_explicit_head_route(client):
    resp = client.head("/health")
    assert_status(resp, 200)
    assert resp.headers.get("x-health") == "ok"


def test_204_preserves_custom_headers(client):
    resp = client.get("/no-content")
    assert_status(resp, 204)
    assert resp.body == b""
    assert resp.headers.get("x-request-id") == "req-42"


def test_304_preserves_headers_and_has_no_body(client):
    resp = client.get("/not-modified")
    assert_status(resp, 304)
    assert resp.body == b""
    assert resp.headers.get("etag") == '"etag-42"'
