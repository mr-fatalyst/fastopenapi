import pytest
from pydantic import BaseModel

from fastopenapi.base_router import SWAGGER_URL, BaseRouter


class DummyModel(BaseModel):
    x: int


class ResponseModel(BaseModel):
    y: int


class NestedModel(BaseModel):
    value: int


class ParentModel(BaseModel):
    nested: NestedModel


def dummy_endpoint_with_annotations(a: str, b: str):
    """Dummy endpoint with query parameters."""
    return {"a": a, "b": b}


def dummy_endpoint_no_annotation(a, b: str):
    """Endpoint where 'a' has no annotation and 'b' is a query parameter."""
    return {"b": b}


def endpoint_with_body(data: DummyModel):
    """Endpoint with request body."""
    return {"data": data.x}


def endpoint_with_meta(a: str):
    """Endpoint with additional meta information."""
    return {"a": a}


@pytest.fixture
def router():
    """Returns an instance of BaseRouter for testing."""
    return BaseRouter(
        docs_url="/docs/",
        openapi_version="3.0.0",
        title="Test App",
        version="0.1.0",
    )


def test_add_and_get_routes(router):
    """Test adding a route and retrieving it."""
    assert router.get_routes() == []

    def ep(a: str):
        return {"a": a}

    router.add_route("/test", "GET", ep)
    routes = router.get_routes()
    assert len(routes) == 1
    path, method, func = routes[0]
    assert path == "/test"
    assert method == "GET"
    assert func is ep


def test_include_router(router):
    """Test including routes from another router."""
    router2 = BaseRouter()

    def ep(a: str):
        return {"a": a}

    router2.add_route("/included", "POST", ep)
    router.include_router(router2)
    routes = router.get_routes()
    assert len(routes) == 1
    assert routes[0][0] == "/included"


def test_decorators(router):
    """Test registration of routes via decorators and meta data assignment."""

    @router.get("/get")
    def get_ep(a: str):
        """GET endpoint."""
        return {"a": a}

    @router.post("/post", tags=["tag1"], status_code=201, response_model=ResponseModel)
    def post_ep(a: str):
        """POST endpoint."""
        return {"a": a}

    routes = router.get_routes()
    assert len(routes) == 2
    meta = getattr(post_ep, "__route_meta__", {})
    assert meta.get("tags") == ["tag1"]
    assert meta.get("status_code") == 201
    assert meta.get("response_model") is ResponseModel


def test_generate_openapi_with_query_parameters(router):
    """Test OpenAPI schema generation for endpoints with query parameters."""

    @router.get("/query")
    def ep(a: str, b: str = "default"):
        """Query endpoint."""
        return {"a": a, "b": b}

    openapi = router.generate_openapi()
    assert openapi["openapi"] == router.openapi_version
    assert "info" in openapi
    assert "/query" in openapi["paths"]
    op = openapi["paths"]["/query"]["get"]
    # If the docstring ends with a period, the generated summary may include it.
    assert op["summary"].startswith("Query endpoint")
    assert "parameters" in op
    params = op["parameters"]
    a_param = next((p for p in params if p["name"] == "a"), None)
    b_param = next((p for p in params if p["name"] == "b"), None)
    assert a_param is not None
    assert a_param["required"] is True
    assert b_param is not None
    assert b_param["required"] is False


def test_generate_openapi_with_request_body(router):
    """
    Test OpenAPI schema generation for endpoints with request body using BaseModel.
    """

    @router.post("/body")
    def ep(data: DummyModel):
        """Body endpoint."""
        return {"data": data.x}

    openapi = router.generate_openapi()
    assert "/body" in openapi["paths"]
    op = openapi["paths"]["/body"]["post"]
    assert ("parameters" not in op) or (op["parameters"] == [])
    assert "requestBody" in op
    req_body = op["requestBody"]
    assert "application/json" in req_body["content"]
    schema = req_body["content"]["application/json"]["schema"]
    assert "properties" in schema
    assert "x" in schema["properties"]


def test_build_operation_with_meta(router):
    """Test _build_operation to verify meta data is applied correctly."""

    def ep(a: str):
        """Test endpoint with meta."""
        return {"a": a}

    ep.__route_meta__ = {
        "tags": ["tagA"],
        "status_code": 202,
        "response_model": ResponseModel,
    }
    definitions = {}
    op = router._build_operation(ep, definitions)
    assert op.get("tags") == ["tagA"]
    assert "202" in op["responses"]
    resp = op["responses"]["202"]
    if "content" in resp:
        assert "application/json" in resp["content"]


def test_render_swagger_ui(router):
    """Test that render_swagger_ui returns HTML with key Swagger UI elements."""
    url = "/openapi.json"
    html = router.render_swagger_ui(url)
    assert "<!DOCTYPE html>" in html
    assert "SwaggerUIBundle" in html
    assert url in html
    assert SWAGGER_URL in html


def test_skip_no_annotation(router):
    """Test that parameters without annotations are skipped in operation building."""
    op = router._build_operation(dummy_endpoint_no_annotation, definitions={})
    params = op.get("parameters", [])
    assert len(params) == 1
    assert params[0]["name"] == "b"


def test_model_schema_definitions(router):
    """
    Test that _get_model_schema removes 'definitions' or
    '$defs' keys and updates definitions dict.
    """
    definitions = {}
    schema = router._get_model_schema(ParentModel, definitions)
    assert "definitions" not in schema and "$defs" not in schema
    assert isinstance(definitions, dict)
    assert len(definitions) > 0


def test_build_operation_without_docstring(router):
    """Test that if an endpoint has no docstring, the generated summary is empty."""

    def ep(a: str):
        return {"a": a}

    ep.__doc__ = None
    op = router._build_operation(ep, definitions={})
    assert op["summary"] == ""


def test_build_operation_with_response_model(router):
    """
    Test that _build_operation applies response_model
    meta correctly in the OpenAPI schema.
    """

    class RespModel(BaseModel):
        y: int

    def ep(a: str):
        return {"a": a}

    ep.__doc__ = "Test endpoint with response model."
    ep.__route_meta__ = {"status_code": 201, "response_model": RespModel}
    definitions = {}
    op = router._build_operation(ep, definitions)
    assert "201" in op["responses"]
    resp = op["responses"]["201"]
    if "content" in resp:
        assert "application/json" in resp["content"]


def test_render_swagger_ui_contains_elements(router):
    """Test that render_swagger_ui returns HTML containing key Swagger UI elements."""
    url = "/openapi.json"
    html = router.render_swagger_ui(url)
    assert "<!DOCTYPE html>" in html
    assert "SwaggerUIBundle" in html
    assert url in html
    assert SWAGGER_URL in html
