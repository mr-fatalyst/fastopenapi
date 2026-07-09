import pytest

from tests.integration.utils import assert_status

pytestmark = pytest.mark.integration


def test_unhandled_exception_does_not_leak_details(client):
    resp = client.get("/boom")
    assert_status(resp, 500)
    assert "SECRET-DETAIL" not in resp.text
