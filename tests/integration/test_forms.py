import pytest

from tests.integration.utils import assert_status, encode_urlencoded

pytestmark = pytest.mark.integration


def test_urlencoded_single_field(client):
    body, ct = encode_urlencoded([("name", "Alice")])
    resp = client.post("/form", content=body, content_type=ct)
    assert_status(resp, 200)
    assert resp.json() == {"name": "Alice", "tags": None}


def test_missing_required_form_field_yields_422(client):
    body, ct = encode_urlencoded([("tags", "a")])
    resp = client.post("/form", content=body, content_type=ct)
    assert_status(resp, 422)


def test_urlencoded_multi_value_field(client):
    # three values so list-append merge paths are exercised too
    body, ct = encode_urlencoded(
        [("name", "Alice"), ("tags", "a"), ("tags", "b"), ("tags", "c")]
    )
    resp = client.post("/form", content=body, content_type=ct)
    assert_status(resp, 200)
    assert resp.json() == {"name": "Alice", "tags": ["a", "b", "c"]}
