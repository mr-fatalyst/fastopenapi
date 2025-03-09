import falcon
import pytest
from falcon import testing

from fastopenapi.routers.falcon import FalconRouter

from .conftest import echo_int, raise_value_error, return_item_model, use_default_param


@pytest.fixture
def falcon_app():
    app = falcon.asgi.App()
    router = FalconRouter(app=app, docs_url="/docs/")
    return app, router


def test_falcon_success_and_validation(falcon_app):
    app, router = falcon_app
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

    client = testing.TestClient(app)
    result = client.simulate_get("/echo", params={"x": "5"})
    assert result.status_code == 200 and result.json == {"x": 5}
    result = client.simulate_get("/echo")
    assert (
        result.status_code == 422
        and "Missing required parameter" in result.json["detail"]
    )
    result = client.simulate_get("/echo", params={"x": "bad"})
    assert result.status_code == 422
    result = client.simulate_get("/path/9")
    assert result.status_code == 200 and result.json == {"x": 9}
    result = client.simulate_get("/path/notanum")
    assert result.status_code == 422
    result = client.simulate_get("/default")
    assert result.status_code == 200 and result.json == {"x": 42}
    item = {"name": "X", "value": 1}
    result = client.simulate_post("/item", json=item)
    assert result.status_code == 200 and result.json == item
    result = client.simulate_post("/item", json={"name": "X"})
    assert (
        result.status_code == 422
        and "Validation error for parameter 'item'" in result.json["detail"]
    )
    result = client.simulate_get("/async", params={"name": "foo"})
    assert result.status_code == 200 and result.json == {"name": "foo"}
    result = client.simulate_get("/sync", params={"name": "bar"})
    assert result.status_code == 200 and result.json == {"name": "bar"}


def test_falcon_exception_handling(falcon_app):
    app, router = falcon_app

    def raise_falcon_http():
        raise falcon.HTTPBadRequest(title="Bad", description="Bad request")

    router.add_route("/error/http", "GET", raise_falcon_http)
    router.add_route("/error/generic", "GET", raise_value_error)

    client = testing.TestClient(app)
    result = client.simulate_get("/error/http")
    assert result.status_code == 400
    assert "Bad request" in (result.text or "")
    result = client.simulate_get("/error/generic")
    assert result.status_code == 422 and result.json["detail"] == "Something went wrong"


def test_falcon_docs_endpoints(falcon_app):
    app, router = falcon_app
    client = testing.TestClient(app)
    result = client.simulate_get("/openapi.json")
    assert result.status_code == 200 and "openapi" in result.json
    result = client.simulate_get("/docs/")
    assert result.status_code == 200
    assert "<title>Swagger UI</title>" in result.text
