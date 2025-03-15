import pytest
from quart import Quart, abort

from fastopenapi.routers import QuartRouter

from .conftest import (
    async_echo_int,
    echo_int,
    echo_int_duplicate,
    raise_value_error,
    return_item_model,
    use_default_param,
)


@pytest.fixture
def quart_app():
    app = Quart(__name__)
    app.testing = True
    router = QuartRouter(app=app)
    return app, router


@pytest.mark.asyncio
async def test_quart_success_and_validation(quart_app):
    app, router = quart_app
    router.add_route("/echo", "GET", echo_int)
    router.add_route("/async_echo", "GET", async_echo_int)
    router.add_route("/path/{x}", "GET", echo_int_duplicate)
    router.add_route("/default", "GET", use_default_param)
    router.add_route("/item", "POST", return_item_model)

    client = app.test_client()

    res = await client.get("/echo?x=123")
    assert res.status_code == 200
    assert await res.get_json() == {"x": 123}

    res = await client.get("/async_echo?x=123")
    assert res.status_code == 200
    assert await res.get_json() == {"x": 123}

    res = await client.get("/echo")
    assert res.status_code == 422
    data = await res.get_json()
    assert data["detail"].startswith("Missing required parameter")

    res = await client.get("/echo?x=abc")
    assert res.status_code == 422
    data = await res.get_json()
    assert "Error casting parameter 'x' to <class 'int'>" in data["detail"]

    res = await client.get("/path/45")
    assert res.status_code == 200
    assert await res.get_json() == {"x": 45}

    res = await client.get("/path/notanum")
    assert res.status_code == 422

    res = await client.get("/default")
    assert res.status_code == 200
    assert await res.get_json() == {"x": 42}

    item_data = {"name": "Item1", "value": 10}
    res = await client.post("/item", json=item_data)
    assert res.status_code == 200
    assert await res.get_json() == item_data

    res = await client.post("/item", json={"name": "Item1"})
    assert res.status_code == 422
    data = await res.get_json()
    assert "Validation error for parameter 'item'" in data["detail"]


@pytest.mark.asyncio
async def test_quart_exception_handling(quart_app):
    app, router = quart_app

    def raise_quart_http():
        abort(404, description="Not found")

    router.add_route("/error/http", "GET", raise_quart_http)
    router.add_route("/error/generic", "GET", raise_value_error)

    client = app.test_client()

    res = await client.get("/error/http")
    assert res.status_code == 404
    data = await res.get_json()
    assert (
        data["code"] == 404
        and data["name"] == "Not Found"
        and "Not found" in data["description"]
    )

    res = await client.get("/error/generic")
    assert res.status_code == 422
    data = await res.get_json()
    assert data["detail"] == "Something went wrong"


@pytest.mark.asyncio
async def test_quart_docs_endpoints(quart_app):
    app, router = quart_app
    client = app.test_client()
    res = await client.get("/openapi.json")
    assert res.status_code == 200
    schema = await res.get_json()
    assert "openapi" in schema and "paths" in schema and "components" in schema

    res = await client.get("/docs")
    assert res.status_code == 200
    data = await res.data
    html_text = data.decode()
    assert "<title>Swagger UI</title>" in html_text
    res = await client.get("/redoc")
    assert res.status_code == 200
    data = await res.data
    html_text = data.decode()
    assert "<title>ReDoc</title>" in html_text


def test_quart_add_route_no_app():
    router = QuartRouter(app=None)

    def dummy_endpoint(x: int):
        return {"x": x}

    router.add_route("/dummy/{x}", "GET", dummy_endpoint)

    routes = router.get_routes()
    assert any(
        path == "/dummy/{x}" and method == "GET" for (path, method, fn) in routes
    )
