import pytest

from tests.integration.utils import assert_status

pytestmark = pytest.mark.integration


def test_multi_value_query_becomes_list(client):
    resp = client.get("/query-multi", query=[("tags", "a"), ("tags", "b")])
    assert_status(resp, 200)
    assert resp.json() == {"tags": ["a", "b"]}


def test_single_value_query_coerced_to_list(client):
    """A single occurrence of a list-typed query param yields a one-item list."""
    resp = client.get("/query-multi", query=[("tags", "a")])
    assert_status(resp, 200)
    assert resp.json() == {"tags": ["a"]}
