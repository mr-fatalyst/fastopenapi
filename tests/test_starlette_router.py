import pytest
from pydantic import BaseModel, ValidationError
from starlette.applications import Starlette
from starlette.testclient import TestClient

from fastopenapi.routers.starlette import StarletteRouter


class SumModel(BaseModel):
    a: int
    b: int


async def get_endpoint(x: str):
    return {"method": "GET", "x": x}


async def post_endpoint(x: str):
    return {"method": "POST", "x": x}


async def put_endpoint(x: str):
    return {"method": "PUT", "x": x}


async def patch_endpoint(x: str):
    return {"method": "PATCH", "x": x}


async def delete_endpoint(x: str):
    return {"method": "DELETE", "x": x}


async def sum_post_endpoint(a: int, b: int):
    try:
        model = SumModel(a=a, b=b)
        return {"sum": model.a + model.b}
    except ValidationError:
        return {"error": "Invalid input"}


@pytest.fixture
def starlette_app():
    app = Starlette()
    router = StarletteRouter(app=app)
    router.add_route("/test/get", "GET", get_endpoint)
    router.add_route("/test/post", "POST", post_endpoint)
    router.add_route("/test/put", "PUT", put_endpoint)
    router.add_route("/test/patch", "PATCH", patch_endpoint)
    router.add_route("/test/delete", "DELETE", delete_endpoint)
    router.add_route("/test/sum", "POST", sum_post_endpoint)
    router.register_routes()
    return app


def test_starlette_endpoints_availability(starlette_app):
    client = TestClient(starlette_app)
    for url in ["/openapi.json", "/docs/"]:
        response = client.get(url)
        assert response.status_code == 200


def test_starlette_methods(starlette_app):
    client = TestClient(starlette_app)
    response = client.get("/test/get?x=hello")
    assert response.status_code == 200
    assert response.json() == {"method": "GET", "x": "hello"}
    response = client.post("/test/post", json={"x": "world"})
    assert response.status_code == 200
    assert response.json() == {"method": "POST", "x": "world"}
    response = client.put("/test/put", json={"x": "put"})
    assert response.status_code == 200
    assert response.json() == {"method": "PUT", "x": "put"}
    response = client.patch("/test/patch", json={"x": "patch"})
    assert response.status_code == 200
    assert response.json() == {"method": "PATCH", "x": "patch"}
    response = client.delete("/test/delete?x=delete")
    assert response.status_code == 200
    assert response.json() == {"method": "DELETE", "x": "delete"}


def test_starlette_valid_schema(starlette_app):
    client = TestClient(starlette_app)
    response = client.post("/test/sum", json={"a": 5, "b": 7})
    assert response.status_code == 200
    assert response.json() == {"sum": 12}


def test_starlette_invalid_schema(starlette_app):
    client = TestClient(starlette_app)
    response = client.post("/test/sum", json={"a": 5})
    assert response.status_code == 422
    assert "detail" in response.json()


def test_starlette_body_exception(monkeypatch, starlette_app):
    from starlette.requests import Request

    async def fake_body(self):
        raise Exception("Forced error")

    monkeypatch.setattr(Request, "body", fake_body)
    client = TestClient(starlette_app)
    response = client.get("/test/get?x=error")
    assert response.status_code == 200
    assert response.json() == {"method": "GET", "x": "error"}
    monkeypatch.undo()


def test_starlette_empty_body(monkeypatch, starlette_app):
    from starlette.requests import Request

    async def empty_body(self):
        return b""

    monkeypatch.setattr(Request, "body", empty_body)
    client = TestClient(starlette_app)
    response = client.get("/test/get?x=empty")
    assert response.status_code == 200
    assert response.json() == {"method": "GET", "x": "empty"}
    monkeypatch.undo()


def test_starlette_include_router(starlette_app):
    from fastopenapi.routers.starlette import StarletteRouter

    sub_router = StarletteRouter(app=starlette_app)

    async def sub_endpoint(x: str):
        return {"sub": x}

    sub_router.add_route("/sub", "GET", sub_endpoint)
    main_router = StarletteRouter(app=starlette_app)
    main_router.include_router(sub_router)
    main_router.register_routes()
    client = TestClient(starlette_app)
    response = client.get("/sub?x=subtest")
    assert response.status_code == 200
    assert response.json() == {"sub": "subtest"}
