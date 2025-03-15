import pytest
from flask import Flask, abort

from fastopenapi.routers import FlaskRouter

from .conftest import (
    echo_int,
    echo_int_duplicate,
    raise_value_error,
    return_item_model,
    use_default_param,
)


@pytest.fixture
def flask_app():
    app = Flask(__name__)
    app.testing = True
    router = FlaskRouter(app=app)
    return app, router


def test_flask_success_and_validation(flask_app):
    app, router = flask_app
    router.add_route("/echo", "GET", echo_int)
    router.add_route("/path/{x}", "GET", echo_int_duplicate)
    router.add_route("/default", "GET", use_default_param)
    router.add_route("/item", "POST", return_item_model)

    client = app.test_client()

    res = client.get("/echo?x=123")
    assert res.status_code == 200
    assert res.get_json() == {"x": 123}

    res = client.get("/echo")
    assert res.status_code == 422
    data = res.get_json()
    assert data["detail"].startswith("Missing required parameter")

    res = client.get("/echo?x=abc")
    assert res.status_code == 422
    data = res.get_json()
    assert "Error casting parameter 'x' to <class 'int'>" in data["detail"]

    res = client.get("/path/45")
    assert res.status_code == 200
    assert res.get_json() == {"x": 45}

    res = client.get("/path/notanum")
    assert res.status_code == 422

    res = client.get("/default")
    assert res.status_code == 200
    assert res.get_json() == {"x": 42}

    item_data = {"name": "Item1", "value": 10}
    res = client.post("/item", json=item_data)
    assert res.status_code == 200
    assert res.get_json() == item_data

    res = client.post("/item", json={"name": "Item1"})
    assert res.status_code == 422
    data = res.get_json()
    assert "Validation error for parameter 'item'" in data["detail"]


def test_flask_exception_handling(flask_app):
    app, router = flask_app

    def raise_flask_http():
        abort(404, description="Not found")

    router.add_route("/error/http", "GET", raise_flask_http)
    router.add_route("/error/generic", "GET", raise_value_error)

    client = app.test_client()

    res = client.get("/error/http")
    assert res.status_code == 404
    data = res.get_json()
    assert (
        data["code"] == 404
        and data["name"] == "Not Found"
        and "Not found" in data["description"]
    )

    res = client.get("/error/generic")
    assert res.status_code == 422
    data = res.get_json()
    assert data["detail"] == "Something went wrong"


def test_flask_docs_endpoints(flask_app):
    app, router = flask_app
    client = app.test_client()
    res = client.get("/openapi.json")
    assert res.status_code == 200
    schema = res.get_json()
    assert "openapi" in schema and "paths" in schema and "components" in schema

    res = client.get("/docs")
    assert res.status_code == 200
    html_text = res.data.decode()
    assert "<title>Swagger UI</title>" in html_text

    res = client.get("/redoc")
    assert res.status_code == 200
    html_text = res.data.decode()
    assert "<title>ReDoc</title>" in html_text


def test_flask_add_route_no_app():
    router = FlaskRouter(app=None)

    def dummy_endpoint(x: int):
        return {"x": x}

    router.add_route("/dummy/{x}", "GET", dummy_endpoint)

    routes = router.get_routes()
    assert any(
        path == "/dummy/{x}" and method == "GET" for (path, method, fn) in routes
    )
