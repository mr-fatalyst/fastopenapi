import pytest

from tests.integration.utils import assert_status

pytestmark = pytest.mark.integration


def test_cookie_param(client):
    resp = client.get("/cookie", cookies={"session": "abc123"})
    assert_status(resp, 200)
    assert resp.json() == {"session": "abc123"}


def test_header_param_underscore_conversion(client):
    resp = client.get("/header", headers={"X-Token": "tok-1"})
    assert_status(resp, 200)
    assert resp.json() == {"x_token": "tok-1"}
