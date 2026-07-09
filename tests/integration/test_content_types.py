import pytest

from tests.integration.utils import assert_status

pytestmark = pytest.mark.integration


def test_bytes_response_defaults_to_octet_stream(client):
    resp = client.get("/binary")
    assert_status(resp, 200)
    assert resp.body == b"\x00\x01BINARY"
    assert resp.headers["content-type"].startswith("application/octet-stream")


def test_str_response_defaults_to_text_plain(client):
    resp = client.get("/plain-text")
    assert_status(resp, 200)
    assert resp.body == b"just text"
    assert resp.headers["content-type"].startswith("text/plain")


def test_explicit_html_content_type_preserved(client):
    resp = client.get("/html")
    assert_status(resp, 200)
    assert resp.body == b"<h1>hi</h1>"
    assert resp.headers["content-type"].startswith("text/html")


def test_explicit_xml_content_type_preserved(client):
    resp = client.get("/xml")
    assert_status(resp, 200)
    assert resp.body == b"<item>1</item>"
    assert resp.headers["content-type"].startswith("application/xml")


def test_tuple_response_with_custom_header(client):
    resp = client.get("/echo-headers", headers={"X-Request-Id": "trace-1"})
    assert_status(resp, 200)
    assert resp.json() == {"received": "trace-1"}
    assert resp.headers.get("x-echo-id") == "trace-1"


def test_json_response_content_type(client):
    resp = client.get("/ping")
    assert_status(resp, 200)
    assert resp.headers["content-type"].startswith("application/json")
