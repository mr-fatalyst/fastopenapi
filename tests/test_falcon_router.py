import json
from http import HTTPStatus

import falcon
import pytest
from falcon import testing

from fastopenapi.routers.falcon import (
    METHODS_MAPPER,
    FalconRouter,
    get_falcon_status,
)

from .conftest import (
    echo,
    echo_int,
    raise_value_error,
    return_item_model,
    use_default_param,
)


class DummyBoundedStream:
    def __init__(self, data: bytes):
        self.data = data

    async def read(self):
        return self.data


class DummyReq:
    def __init__(self, data: bytes = b""):
        self.bounded_stream = DummyBoundedStream(data)
        self.params = {}


class DummyReqException:
    class DummyBoundedStream:
        async def read(self):
            raise Exception("read error")

    def __init__(self):
        self.bounded_stream = self.DummyBoundedStream()
        self.params = {}


class DummyResp:
    def __init__(self):
        self.status = None
        self.media = None
        self.content_type = None
        self.text = None


class DummyApp:
    def __init__(self):
        self.routes = {}

    def add_route(self, path, resource):
        self.routes[path] = resource


class DummyReqDirect:
    def __init__(self, data: bytes = b""):
        class DummyBoundedStream:
            def __init__(self, data):
                self.data = data

            async def read(self):
                return self.data

        self.bounded_stream = DummyBoundedStream(data)
        self.params = {}


class DummyRespDirect:
    def __init__(self):
        self.status = None
        self.media = None
        self.content_type = None
        self.text = None


@pytest.fixture
def falcon_app():
    app = falcon.asgi.App()
    router = FalconRouter(app=app)
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
    result = client.simulate_get("/docs")
    assert result.status_code == 200
    assert "<title>Swagger UI</title>" in result.text
    result = client.simulate_get("/redoc")
    assert result.status_code == 200
    assert "<title>ReDoc</title>" in result.text


def test_get_falcon_status_unknown():
    assert get_falcon_status(HTTPStatus(418)) == falcon.HTTP_500


@pytest.mark.asyncio
async def test_read_body_valid():
    router = FalconRouter(app=None)
    data = json.dumps({"key": "value"}).encode("utf-8")
    req = DummyReq(data)
    body = await router._read_body(req)
    assert body == {"key": "value"}


@pytest.mark.asyncio
async def test_read_body_empty():
    router = FalconRouter(app=None)
    req = DummyReq(b"")
    body = await router._read_body(req)
    assert body == {}


@pytest.mark.asyncio
async def test_read_body_exception():
    router = FalconRouter(app=None)
    req = DummyReqException()
    body = await router._read_body(req)
    assert body == {}


def test_handle_error():
    router = FalconRouter(app=None)
    resp = DummyResp()
    error_message = "Error occurred"
    router._handle_error(resp, error_message)
    assert resp.status == falcon.HTTP_422
    assert resp.media == {"detail": error_message}


def test_create_or_update_resource_reuse():
    app = DummyApp()
    router = FalconRouter(app=app)

    resource1 = router._create_or_update_resource("/test", "GET", echo)
    setattr(resource1, "dummy", "value")
    resource2 = router._create_or_update_resource("/test", "GET", echo)
    assert resource1 is resource2
    assert hasattr(resource2, METHODS_MAPPER["GET"])


def test_register_docs_endpoints():
    app = DummyApp()
    router = FalconRouter(app=app)
    router._openapi_schema = {"openapi": "3.0.0"}
    router.render_swagger_ui = lambda url: "<html>Swagger UI</html>"
    router._register_docs_endpoints()
    assert "/openapi.json" in app.routes
    assert "/docs" in app.routes


@pytest.mark.asyncio
async def test_handle_request_reraises_falcon_http_error_async():
    async def endpoint_raise_async(x: int):
        raise falcon.HTTPBadRequest(title="Bad", description="Bad request")

    req = DummyReq(b"")
    resp = DummyResp()
    router = FalconRouter(app=None)
    router.resolve_endpoint_params = lambda endpoint, all_params, body: {"x": 1}

    with pytest.raises(falcon.HTTPBadRequest) as exc_info:
        await router._handle_request(endpoint_raise_async, req, resp, x="1")
    assert "bad request" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_handle_request_reraises_http_error_sync():
    def endpoint_raise(x: int):
        raise falcon.HTTPBadRequest(title="Bad", description="Bad request")

    req = DummyReq(b"")
    resp = DummyResp()
    router = FalconRouter(app=None)
    router.resolve_endpoint_params = lambda endpoint, all_params, body: {"x": 1}

    with pytest.raises(falcon.HTTPBadRequest) as exc_info:
        await router._handle_request(endpoint_raise, req, resp, x="1")
    exc_str = str(exc_info.value).lower()
    assert "bad" in exc_str
    assert "bad request" in exc_str
