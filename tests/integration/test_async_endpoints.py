"""Async endpoints across all async-capable framework variants.

Sync-only routers (flask, falcon, django) reject async endpoints at
registration, so these scenarios are skipped for them.
"""

import pytest

from tests.integration.utils import assert_status

pytestmark = pytest.mark.integration

SYNC_ONLY = {"flask", "falcon", "django"}


def _skip_sync_only(client):
    if client.framework in SYNC_ONLY:
        pytest.skip(f"{client.framework}: sync-only router")


def test_async_endpoint(client):
    _skip_sync_only(client)
    resp = client.get("/async-ping")
    assert_status(resp, 200)
    assert resp.json() == {"ping": "async-pong"}


def test_async_endpoint_with_body_and_async_dependency(client):
    _skip_sync_only(client)
    resp = client.post("/async-echo", json_body={"name": "x", "price": 1.5})
    assert_status(resp, 200)
    assert resp.json() == {"name": "x", "source": "async-dep"}


def test_async_generator_dependency(client):
    _skip_sync_only(client)
    resp = client.get("/async-gen")
    assert_status(resp, 200)
    assert resp.json() == {"value": "async-gen"}
