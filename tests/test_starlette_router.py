import pytest
from starlette.applications import Starlette
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.testclient import TestClient

from fastopenapi.routers.starlette import StarletteRouter

from .conftest import echo_int, raise_value_error, return_item_model, use_default_param


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
