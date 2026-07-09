import pytest

from tests.integration.utils import assert_status

pytestmark = pytest.mark.integration


def test_ping(client):
    resp = client.get("/ping")
    assert_status(resp, 200)
    assert resp.json() == {"ping": "pong"}
