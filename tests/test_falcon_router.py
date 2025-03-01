import falcon.asgi
import pytest
from falcon.testing import TestClient
from pydantic import BaseModel, ValidationError

from fastopenapi.routers.falcon import FalconRouter


class SumModel(BaseModel):
    a: int
    b: int


class DummyResponse(BaseModel):
    msg: str


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
    try:
        model = SumModel(a=a, b=b)
        return {"sum": model.a + model.b}
    except ValidationError:
        return {"error": "Invalid input"}


def model_endpoint(x: str):
    # Returns a pydantic model to test conversion to dict.
    return DummyResponse(msg=x)


@pytest.fixture
def falcon_app():
    app = falcon.asgi.App()
    router = FalconRouter(app=app)
    router.get("/test/get")(get_endpoint)
    router.post("/test/post")(post_endpoint)
    router.put("/test/put")(put_endpoint)
    router.patch("/test/patch")(patch_endpoint)
    router.delete("/test/delete")(delete_endpoint)
    router.post("/test/sum")(sum_post_endpoint)
    router.get("/test/model")(model_endpoint)
    return app


def test_falcon_endpoints_availability(falcon_app):
    client = TestClient(falcon_app)
    for url in ["/openapi.json", "/docs/"]:
        response = client.simulate_get(url)
        assert response.status_code == 200


def test_falcon_methods(falcon_app):
    client = TestClient(falcon_app)
    response = client.simulate_get("/test/get", params={"x": "hello"})
    assert response.status_code == 200
    assert response.json == {"method": "GET", "x": "hello"}
    response = client.simulate_post("/test/post", json={"x": "world"})
    assert response.status_code == 200
    assert response.json == {"method": "POST", "x": "world"}
    response = client.simulate_put("/test/put", json={"x": "put"})
    assert response.status_code == 200
    assert response.json == {"method": "PUT", "x": "put"}
    response = client.simulate_patch("/test/patch", json={"x": "patch"})
    assert response.status_code == 200
    assert response.json == {"method": "PATCH", "x": "patch"}
    response = client.simulate_delete("/test/delete", params={"x": "delete"})
    assert response.status_code == 200
    assert response.json == {"method": "DELETE", "x": "delete"}


def test_falcon_valid_schema(falcon_app):
    client = TestClient(falcon_app)
    response = client.simulate_post("/test/sum", json={"a": 5, "b": 7})
    assert response.status_code == 200
    assert response.json == {"sum": 12}


def test_falcon_invalid_schema(falcon_app):
    client = TestClient(falcon_app)
    # Missing 'b' leads to TypeError caught by router and returns 422.
    response = client.simulate_post("/test/sum", json={"a": 5})
    assert response.status_code == 422
    assert "detail" in response.json


def test_falcon_invalid_type_schema(falcon_app):
    client = TestClient(falcon_app)
    # Passing invalid types so that pydantic raises ValidationError.
    response = client.simulate_post("/test/sum", json={"a": "foo", "b": "bar"})
    # Endpoint catches ValidationError and returns error dict.
    assert response.status_code == 200
    assert response.json == {"error": "Invalid input"}


def test_falcon_model_response(falcon_app):
    client = TestClient(falcon_app)
    # Test endpoint returning a pydantic model.
    response = client.simulate_get("/test/model", params={"x": "model"})
    assert response.status_code == 200
    assert response.json == {"msg": "model"}


def test_falcon_body_exception(monkeypatch, falcon_app):
    from falcon.asgi import Request

    class FakeBoundedStream:
        async def read(self):
            raise Exception("Forced exception")

    monkeypatch.setattr(
        Request, "bounded_stream", property(lambda self: FakeBoundedStream())
    )
    client = TestClient(falcon_app)
    response = client.simulate_get("/test/get", params={"x": "hello"})
    assert response.status_code == 200


def test_falcon_body_merging(falcon_app):
    def merge_endpoint(z: str):
        return {"z": z}

    router = FalconRouter(app=falcon_app)
    router.add_route("/merge", "POST", merge_endpoint)
    client = TestClient(falcon_app)
    response = client.simulate_post("/merge?z=query", json={"z": "body"})
    assert response.status_code == 200
    assert response.json == {"z": "body"}


def test_falcon_empty_body(monkeypatch, falcon_app):
    # Test branch where the body is empty; no update to parameters.
    from falcon.asgi import Request

    class FakeBoundedStream:
        async def read(self):
            return b""

    monkeypatch.setattr(
        Request, "bounded_stream", property(lambda self: FakeBoundedStream())
    )
    client = TestClient(falcon_app)
    response = client.simulate_get("/test/get", params={"x": "empty"})
    assert response.status_code == 200
    assert response.json == {"method": "GET", "x": "empty"}
