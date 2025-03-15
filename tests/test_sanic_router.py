import pytest
from sanic import Sanic
from sanic.exceptions import HTTPException, InvalidUsage

from fastopenapi.routers import SanicRouter

from .conftest import echo_int, raise_value_error, return_item_model, use_default_param


@pytest.fixture
def sanic_app():
    app = Sanic("test_app")
    router = SanicRouter(app=app, docs_url="/docs/")
    try:
        from sanic_testing import TestManager

        TestManager(app)
    except ImportError:
        pytest.skip("sanic-testing not installed")
    return app, router


def test_sanic_success_and_validation(sanic_app):
    app, router = sanic_app
    router.add_route("/echo", "GET", echo_int)
    router.add_route("/path/<x>", "GET", echo_int)
    router.add_route("/default", "GET", use_default_param)
    router.add_route("/item", "POST", return_item_model)

    async def async_echo(name: str):
        return {"name": name}

    def sync_echo(name: str):
        return {"name": name}

    router.add_route("/async", "GET", async_echo)
    router.add_route("/sync", "GET", sync_echo)

    client = app.test_client
    request, response_obj = client.get("/echo?x=3")
    assert response_obj.status == 200 and response_obj.json == {"x": 3}
    request, response_obj = client.get("/echo")
    assert (
        response_obj.status == 422
        and "Missing required parameter" in response_obj.json.get("detail", "")
    )
    request, response_obj = client.get("/echo?x=bad")
    assert (
        response_obj.status == 422
        and "Error casting parameter 'x'" in response_obj.json.get("detail", "")
    )
    request, response_obj = client.get("/path/7")
    assert response_obj.status == 200 and response_obj.json == {"x": 7}
    request, response_obj = client.get("/path/notanum")
    assert response_obj.status == 422
    request, response_obj = client.get("/default")
    assert response_obj.status == 200 and response_obj.json == {"x": 42}
    request, response_obj = client.post("/item", json={"name": "A", "value": 1})
    assert response_obj.status == 200 and response_obj.json == {"name": "A", "value": 1}
    request, response_obj = client.post("/item", json={"name": "A"})
    assert (
        response_obj.status == 422
        and "Validation error for parameter 'item'"
        in response_obj.json.get("detail", "")
    )
    request, response_obj = client.get("/async?name=test")
    assert response_obj.status == 200 and response_obj.json == {"name": "test"}
    request, response_obj = client.get("/sync?name=test")
    assert response_obj.status == 200 and response_obj.json == {"name": "test"}


def test_sanic_exception_handling(sanic_app):
    app, router = sanic_app

    def raise_sanic_http(request):
        raise InvalidUsage("Bad request")

    router.add_route("/error/http", "GET", raise_sanic_http)
    router.add_route("/error/generic", "GET", raise_value_error)
    client = app.test_client

    request, response_obj = client.get("/error/http")
    assert response_obj.status == 422
    data = response_obj.json
    assert data["detail"] == "Missing required parameter: 'request'"
    request, response_obj = client.get("/error/generic")
    assert (
        response_obj.status == 422
        and response_obj.json.get("detail") == "Something went wrong"
    )


def test_sanic_docs_endpoints(sanic_app):
    app, router = sanic_app
    client = app.test_client
    request, response_obj = client.get("/openapi.json")
    assert response_obj.status == 200
    schema = response_obj.json
    assert "openapi" in schema and "paths" in schema
    request, response_obj = client.get("/docs/")
    assert response_obj.status == 200
    text = response_obj.text
    assert "<title>Swagger UI</title>" in text


def test_add_route_with_no_app():
    router = SanicRouter(app=None)

    def dummy(x: int):
        return {"x": x}

    router.add_route("/no_app", "GET", dummy)
    routes = router.get_routes()
    assert any(r[0] == "/no_app" for r in routes)


def test_http_exception_in_endpoint(sanic_app):
    app, router = sanic_app

    def endpoint_http(x: int):
        raise HTTPException("HTTP Error")

    router.add_route("/http_error", "GET", endpoint_http)
    client = app.test_client
    request, response_obj = client.get("/http_error?x=5")
    data = response_obj.json
    assert data["description"] == "HTTP Error"
    assert data["status"] == 500
    assert "HTTP Error" in data["message"]
