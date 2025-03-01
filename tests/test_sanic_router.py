import json
import uuid

import pytest
from pydantic import BaseModel, ValidationError
from sanic import Sanic

from fastopenapi.routers.sanic import SanicRouter


class SumModel(BaseModel):
    a: int
    b: int


def get_endpoint(x: str):
    return {"method": "GET", "x": x}


def post_endpoint(x: str):
    return {"method": "POST", "x": x}


def put_endpoint(x: str):
    return {"method": "PUT", "x": x}


def patch_endpoint(x: str):
    return {"method": "PATCH", "x": x}


def delete_endpoint(x: str):
    return {"method": "DELETE", "x": x}


def sum_post_endpoint(a: int, b: int):
    """
    If b is missing => TypeError => router => 422
    If a,b invalid => pydantic => {"error":"Invalid input"}
    """
    try:
        model = SumModel(a=a, b=b)
        return {"sum": model.a + model.b}
    except ValidationError:
        return {"error": "Invalid input"}


def model_endpoint(x: str):
    return {"msg": x}


def merge_endpoint(z: str):
    """Check that JSON overrides query param."""
    return {"z": z}


async def async_endpoint_with_params(x: str, y: str):
    """
    If y is missing => TypeError => 422 branch in router.
    We parse y to int => test expects {'y': 333}.
    """
    return {"method": "ASYNC", "x": x, "y": int(y)}


class NoDocsSanicRouter(SanicRouter):
    """Subclass that disables docs endpoints."""

    def _register_docs_endpoints(self):
        pass


@pytest.fixture
def sanic_app_docs():
    """App with docs_url='/docs/'"""
    app = Sanic("app_docs_" + str(uuid.uuid4()))
    router = SanicRouter(app=app, docs_url="/docs/")
    router.get("/test/get")(get_endpoint)
    router.post("/test/post")(post_endpoint)
    router.put("/test/put")(put_endpoint)
    router.patch("/test/patch")(patch_endpoint)
    router.delete("/test/delete")(delete_endpoint)
    router.post("/test/sum")(sum_post_endpoint)
    router.get("/test/model")(model_endpoint)
    router.post("/merge")(merge_endpoint)
    router.get("/test/async")(async_endpoint_with_params)
    return app


@pytest.fixture
def sanic_app_nodocs():
    """App with docs disabled"""
    app = Sanic("app_nodocs_" + str(uuid.uuid4()))
    router = NoDocsSanicRouter(app=app, docs_url="")
    router.get("/test/get")(get_endpoint)
    router.post("/test/post")(post_endpoint)
    router.put("/test/put")(put_endpoint)
    router.patch("/test/patch")(patch_endpoint)
    router.delete("/test/delete")(delete_endpoint)
    router.post("/test/sum")(sum_post_endpoint)
    router.get("/test/model")(model_endpoint)
    return app


@pytest.mark.asyncio
async def test_docs_availability(sanic_app_docs):
    """Check /openapi.json, /docs/ => 200."""
    client = sanic_app_docs.asgi_client
    req, resp = await client.get("/openapi.json")
    assert resp.status == 200
    req, resp = await client.get("/docs/")
    assert resp.status == 200


@pytest.mark.asyncio
async def test_methods(sanic_app_docs):
    """GET, POST, PUT, PATCH, DELETE."""
    client = sanic_app_docs.asgi_client

    req, resp = await client.get("/test/get?x=hello")
    assert resp.status == 200
    assert resp.json == {"method": "GET", "x": "hello"}

    req, resp = await client.post("/test/post", json={"x": "world"})
    assert resp.status == 200
    assert resp.json == {"method": "POST", "x": "world"}

    req, resp = await client.put("/test/put", json={"x": "put"})
    assert resp.status == 200
    assert resp.json == {"method": "PUT", "x": "put"}

    req, resp = await client.patch("/test/patch", json={"x": "patch"})
    assert resp.status == 200
    assert resp.json == {"method": "PATCH", "x": "patch"}

    req, resp = await client.delete("/test/delete?x=delete")
    assert resp.status == 200
    assert resp.json == {"method": "DELETE", "x": "delete"}


@pytest.mark.asyncio
async def test_sum_valid(sanic_app_docs):
    client = sanic_app_docs.asgi_client
    req, resp = await client.post("/test/sum", json={"a": 5, "b": 7})
    assert resp.status == 200
    assert resp.json == {"sum": 12}


@pytest.mark.asyncio
async def test_sum_missing_param(sanic_app_docs):
    """Missing b => TypeError => 422."""
    client = sanic_app_docs.asgi_client
    req, resp = await client.post("/test/sum", json={"a": 5})
    assert resp.status == 422
    assert "detail" in resp.json


@pytest.mark.asyncio
async def test_sum_invalid_type(sanic_app_docs):
    """a,b invalid => ValidationError => {'error':'Invalid input'}"""
    client = sanic_app_docs.asgi_client
    req, resp = await client.post("/test/sum", json={"a": "foo", "b": "bar"})
    assert resp.status == 200
    assert resp.json == {"error": "Invalid input"}


@pytest.mark.asyncio
async def test_model_endpoint(sanic_app_docs):
    """GET /test/model => {'msg': x}"""
    client = sanic_app_docs.asgi_client
    req, resp = await client.get("/test/model?x=some")
    assert resp.status == 200
    assert resp.json == {"msg": "some"}


@pytest.mark.asyncio
async def test_empty_body(sanic_app_docs):
    """POST /test/sum?a=5&b=7 + data='' => sum=12."""
    client = sanic_app_docs.asgi_client
    req, resp = await client.post("/test/sum?a=5&b=7", data="")
    assert resp.status == 200
    assert resp.json == {"sum": 12}


@pytest.mark.asyncio
async def test_no_docs_availability(sanic_app_nodocs):
    """docs_url="", expect 404 for /openapi.json, /docs/."""
    client = sanic_app_nodocs.asgi_client
    req, resp = await client.get("/openapi.json")
    assert resp.status == 404
    req, resp = await client.get("/docs/")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_body_merging(sanic_app_docs):
    """POST /merge?z=query + json={'z':'body'} => z='body'."""
    client = sanic_app_docs.asgi_client
    req, resp = await client.post("/merge?z=query", json={"z": "body"})
    assert resp.status == 200
    assert resp.json == {"z": "body"}


@pytest.mark.asyncio
async def test_async_endpoint_ok(sanic_app_docs):
    """
    GET /test/async?x=async&y=333 => parse y as int => y=333
    """
    client = sanic_app_docs.asgi_client
    req, resp = await client.get("/test/async?x=async&y=333")
    assert resp.status == 200
    assert resp.json == {"method": "ASYNC", "x": "async", "y": 333}


@pytest.mark.asyncio
async def test_async_endpoint_missing_param(sanic_app_docs):
    """
    GET /test/async?x=missing => y param => TypeError => 422
    """
    client = sanic_app_docs.asgi_client
    req, resp = await client.get("/test/async?x=missing")
    assert resp.status == 422
    assert "detail" in resp.json


@pytest.mark.asyncio
async def test_forced_body_exception(sanic_app_docs, monkeypatch):
    original_loads = json.loads

    def raising_loads(*args, **kwargs):
        raise Exception("Forced body error")

    monkeypatch.setattr(json, "loads", raising_loads)

    client = sanic_app_docs.asgi_client
    req, resp = await client.post("/test/post", json={"x": "error"})
    assert resp.status == 200
    monkeypatch.setattr(json, "loads", original_loads)
