import json

import pytest
from starlette.applications import Starlette
from starlette.datastructures import QueryParams
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse
from starlette.testclient import TestClient

from fastopenapi.routers import StarletteRouter

from .conftest import (
    echo_both,
    echo_int,
    raise_value_error,
    return_item_model,
    use_default_param,
)


class DummyRequestFailBody:
    async def body(self):
        raise Exception("Simulated failure in body")

    @property
    def query_params(self):
        return QueryParams({"x": "42"})

    @property
    def path_params(self):
        return {}


@pytest.fixture
def starlette_app():
    app = Starlette()
    router = StarletteRouter(app=app, docs_url="/docs/")
    return app, router


def test_starlette_success_and_validation(starlette_app):
    app, router = starlette_app
    router.add_route("/echo", "GET", echo_int)
    router.add_route("/path/{x}", "GET", echo_int)
    router.add_route("/default", "GET", use_default_param)
    router.add_route("/item", "POST", return_item_model)

    async def async_echo(name: str):
        return {"name": name}

    def sync_echo(name: str):
        return {"name": name}

    router.add_route("/async", "GET", async_echo)
    router.add_route("/sync", "GET", sync_echo)

    client = TestClient(app)

    res = client.get("/echo?x=7")
    assert res.status_code == 200 and res.json() == {"x": 7}
    res = client.get("/echo")
    assert res.status_code == 422
    res = client.get("/echo?x=bad")
    assert res.status_code == 422
    res = client.get("/path/11")
    assert res.status_code == 200 and res.json() == {"x": 11}
    res = client.get("/path/notanum")
    assert res.status_code == 422
    res = client.get("/default")
    assert res.status_code == 200 and res.json() == {"x": 42}
    item = {"name": "ItemX", "value": 99}
    res = client.post("/item", json=item)
    assert res.status_code == 200 and res.json() == item
    res = client.post("/item", json={"name": "ItemX"})
    assert (
        res.status_code == 422
        and "Validation error for parameter 'item'" in res.json()["detail"]
    )
    res = client.get("/async?name=foo")
    assert res.status_code == 200 and res.json() == {"name": "foo"}
    res = client.get("/sync?name=bar")
    assert res.status_code == 200 and res.json() == {"name": "bar"}


def test_starlette_exception_handling(starlette_app):
    app, router = starlette_app

    def raise_starlette_http():
        raise StarletteHTTPException(status_code=400, detail="Bad request")

    router.add_route("/error/http", "GET", raise_starlette_http)
    router.add_route("/error/generic", "GET", raise_value_error)

    client = TestClient(app)
    res = client.get("/error/http")
    assert res.status_code == 400
    data = res.json()
    assert data["status"] == 400 and data["description"] == "Bad request"
    res = client.get("/error/generic")
    assert res.status_code == 422 and res.json()["detail"] == "Something went wrong"


def test_starlette_docs_endpoints(starlette_app):
    app, router = starlette_app
    client = TestClient(app)
    res = client.get("/openapi.json")
    assert res.status_code == 200 and "openapi" in res.json()
    res = client.get("/docs/")
    assert res.status_code == 200
    text = res.text
    assert "<title>Swagger UI</title>" in text


def test_starlette_echo_both(starlette_app):
    app, router = starlette_app
    router.add_route("/both", "POST", echo_both)
    client = TestClient(app)
    res = client.post("/both?x=10", json={"name": "Test", "value": 123})
    assert res.status_code == 200
    assert res.json() == {"x": 10, "item": {"name": "Test", "value": 123}}


def test_starlette_add_route_no_app():
    router = StarletteRouter(app=None, docs_url="/docs/", openapi_url="/openapi.json")
    router.add_route("/no_app", "GET", echo_int)
    assert any(route.path == "/no_app" for route in router._routes_starlette)


@pytest.mark.asyncio
async def test_starlette_view_body_exception_direct():
    router = StarletteRouter(app=None, docs_url="/docs/", openapi_url="/openapi.json")
    router.resolve_endpoint_params = lambda endpoint, all_params, body: {
        "x": int(all_params.get("x", 0))
    }

    def dummy_endpoint(x: int):
        return {"x": x}

    dummy_req = DummyRequestFailBody()
    response = await StarletteRouter._starlette_view(dummy_req, router, dummy_endpoint)
    assert isinstance(response, JSONResponse)
    data = json.loads(response.body.decode())
    assert data == {"x": 42}
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_handle_exceptions_no_detail():
    class DummyRequest:
        pass

    dummy_req = DummyRequest()
    exc = StarletteHTTPException(status_code=500, detail=None)
    response = await StarletteRouter.handle_exceptions(dummy_req, exc)
    data = json.loads(response.body.decode())
    assert data["description"] == "Internal Server Error"
    assert data["status"] == 500
    assert "Internal Server Error" in data["message"]
