import pytest
from flask import Flask
from pydantic import BaseModel, ValidationError

from fastopenapi.routers.flask import FlaskRouter


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
    try:
        model = SumModel(a=a, b=b)
        return {"sum": model.a + model.b}
    except ValidationError:
        return {"error": "Invalid input"}


@pytest.fixture
def flask_app():
    app = Flask(__name__)
    router = FlaskRouter(app=app)
    router.get("/test/get")(get_endpoint)
    router.post("/test/post")(post_endpoint)
    router.put("/test/put")(put_endpoint)
    router.patch("/test/patch")(patch_endpoint)
    router.delete("/test/delete")(delete_endpoint)
    router.post("/test/sum")(sum_post_endpoint)
    return app


def test_flask_endpoints_availability(flask_app):
    client = flask_app.test_client()
    for url in ["/openapi.json", "/docs/"]:
        response = client.get(url)
        assert response.status_code == 200


def test_flask_methods(flask_app):
    client = flask_app.test_client()
    response = client.get("/test/get", query_string={"x": "hello"})
    assert response.status_code == 200
    assert response.get_json() == {"method": "GET", "x": "hello"}

    response = client.post("/test/post", json={"x": "world"})
    assert response.status_code == 200
    assert response.get_json() == {"method": "POST", "x": "world"}

    response = client.put("/test/put", json={"x": "put"})
    assert response.status_code == 200
    assert response.get_json() == {"method": "PUT", "x": "put"}

    response = client.patch("/test/patch", json={"x": "patch"})
    assert response.status_code == 200
    assert response.get_json() == {"method": "PATCH", "x": "patch"}

    response = client.delete("/test/delete", query_string={"x": "delete"})
    assert response.status_code == 200
    assert response.get_json() == {"method": "DELETE", "x": "delete"}


def test_flask_valid_schema(flask_app):
    client = flask_app.test_client()
    response = client.post("/test/sum", json={"a": 5, "b": 7})
    assert response.status_code == 200
    assert response.get_json() == {"sum": 12}


def test_flask_invalid_schema(flask_app):
    client = flask_app.test_client()
    response = client.post("/test/sum", json={"a": 5})
    assert response.status_code == 422
    assert "detail" in response.get_json()


def test_flask_no_json_body(flask_app):
    client = flask_app.test_client()
    response = client.post(
        "/test/sum?a=2&b=3", data="", content_type="application/json"
    )
    # sum=5
    assert response.status_code == 200
    assert response.get_json() == {"sum": 5}


def test_flask_broken_json(flask_app):
    client = flask_app.test_client()
    bad_json = '{"a": 5,,}'
    response = client.post("/test/sum", data=bad_json, content_type="application/json")
    assert response.status_code == 422
    assert "detail" in response.get_json()


def test_flask_include_router():
    app = Flask(__name__)
    main_router = FlaskRouter(app=app)

    sub_router = FlaskRouter(app=None)  # no app yet

    def sub_endpoint(z: str):
        return {"sub": z}

    sub_router.get("/sub")(sub_endpoint)

    main_router.include_router(sub_router)  # include routes
    client = app.test_client()
    resp = client.get("/sub", query_string={"z": "hello"})
    assert resp.status_code == 200
    assert resp.get_json() == {"sub": "hello"}


def test_flask_no_app():
    router = FlaskRouter(app=None)
    router.get("/no_app")(lambda: {"msg": "no app"})
    routes = router.get_routes()
    assert len(routes) == 1
    path, method, func = routes[0]
    assert path == "/no_app"
    assert method == "GET"
