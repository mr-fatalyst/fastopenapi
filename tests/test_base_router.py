import pytest
from pydantic import BaseModel

from fastopenapi.base_router import SWAGGER_URL, BaseRouter

from .conftest import Item, echo_int, return_item_model


class DummyRouter(BaseRouter):
    def _register_docs_endpoints(self):
        pass


class DummyModel(BaseModel):
    field: int


def endpoint_no_annotation(param, a: int):
    return param, a


def test_resolve_endpoint_params_success_and_failure():
    router = BaseRouter()

    def func_required(a: int):
        return a

    def func_optional(b: int = 5):
        return b

    def func_model(m: Item):
        return m

    def func_no_anno(param):
        return param

    kwargs = router.resolve_endpoint_params(func_required, {"a": "10"}, {})
    assert kwargs == {"a": 10}

    with pytest.raises(ValueError) as excinfo:
        router.resolve_endpoint_params(func_required, {}, {})
    assert "Missing required parameter" in str(excinfo.value)

    kwargs = router.resolve_endpoint_params(func_optional, {}, {})
    assert kwargs == {"b": 5}

    with pytest.raises(ValueError) as excinfo:
        router.resolve_endpoint_params(func_required, {"a": "not_an_int"}, {})
    assert "Error casting parameter 'a'" in str(excinfo.value)

    body = {"name": "Test", "value": 123}
    kwargs = router.resolve_endpoint_params(func_model, {}, body)
    assert isinstance(kwargs["m"], Item)
    assert kwargs["m"].name == "Test" and kwargs["m"].value == 123

    bad_body = {"name": "x"}
    with pytest.raises(ValueError) as excinfo:
        router.resolve_endpoint_params(func_model, {}, bad_body)
    assert "Validation error for parameter 'm'" in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        router.resolve_endpoint_params(func_no_anno, {"param": "foo"}, {})
    assert "Error casting parameter 'param'" in str(excinfo.value)

    with pytest.raises(ValueError):
        router.resolve_endpoint_params(func_no_anno, {}, {})


def test_route_decorators_attach_meta_and_add_route():
    router = BaseRouter()

    @router.get("/test_get", tags=["Test"], status_code=201, response_model=Item)
    def get_endpoint():
        """Docstring for get."""
        return {}

    @router.post("/test_post", tags=["Test"], status_code=200)
    def post_endpoint(item: Item):
        return item

    routes = router.get_routes()
    paths_methods = {(path, method) for (path, method, fn) in routes}
    assert ("/test_get", "GET") in paths_methods
    assert ("/test_post", "POST") in paths_methods

    assert hasattr(get_endpoint, "__route_meta__")
    meta = get_endpoint.__route_meta__
    assert (
        meta["tags"] == ["Test"]
        and meta["status_code"] == 201
        and meta["response_model"] == Item
    )

    assert get_endpoint.__doc__ == "Docstring for get."


def test_include_router_combines_routes_with_prefix():
    main_router = BaseRouter()
    sub_router = BaseRouter()
    sub_router.add_route("/subpath", "GET", echo_int)
    sub_router.add_route("subno_slash", "POST", return_item_model)
    main_router.include_router(sub_router, prefix="/api")
    routes = main_router.get_routes()
    paths = {path for (path, _, _) in routes}
    assert "/api/subpath" in paths
    assert "/api/subno_slash" in paths


def test_generate_openapi_schema():
    router = BaseRouter()

    @router.get("/items/{item_id}", tags=["Items"], status_code=200)
    def get_item(item_id: int):
        """Get item by ID."""
        return {"item_id": item_id}

    @router.get("/filter", tags=["Items"])
    def filter_items(filter: Item):
        """Filter items by query parameters."""
        return []

    @router.post("/items", tags=["Items"], status_code=201, response_model=Item)
    def create_item(item: Item):
        """Create a new item."""
        return item

    @router.get("/items", tags=["Items"], response_model=list[Item])
    def list_items():
        """List items."""
        return []

    schema = router.openapi

    assert schema["openapi"] == router.openapi_version
    assert (
        schema["info"]["title"] == router.title
        and schema["info"]["version"] == router.version
    )

    assert "Item" in schema["components"]["schemas"]

    params = schema["paths"]["/items/{item_id}"]["get"]["parameters"]
    param = next((p for p in params if p["name"] == "item_id"), None)
    assert (
        param
        and param["in"] == "path"
        and param["required"] is True
        and param["schema"]["type"] == "integer"
    )

    filter_params = schema["paths"]["/filter"]["get"]["parameters"]
    names = {p["name"] for p in filter_params}
    assert "name" in names and "value" in names

    post_op = schema["paths"]["/items"]["post"]
    assert "requestBody" in post_op
    schema_ref = post_op["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    assert schema_ref.endswith("/Item")

    responses_post = post_op["responses"]
    responses_get = schema["paths"]["/items"]["get"]["responses"]
    assert responses_post["201"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("/Item")
    schema_200 = responses_get["200"]["content"]["application/json"]["schema"]
    assert schema_200["type"] == "array" and schema_200["items"]["$ref"].endswith(
        "/Item"
    )

    op_get_item = schema["paths"]["/items/{item_id}"]["get"]
    assert op_get_item["tags"] == ["Items"]
    assert op_get_item["summary"] == "Get item by ID."
    op_list_items = schema["paths"]["/items"]["get"]
    assert op_list_items["responses"]["200"]["description"]

    schema2 = router.openapi
    assert schema2 is schema


def test_serialize_response_model():
    model_instance = Item(name="Test", value=42)
    serialized = BaseRouter._serialize_response(model_instance)
    assert isinstance(serialized, dict)
    assert serialized == model_instance.model_dump()


def test_serialize_response_list():
    models = [Item(name="Test1", value=1), Item(name="Test2", value=2)]
    serialized = BaseRouter._serialize_response(models)
    assert isinstance(serialized, list)
    for orig, ser in zip(models, serialized):
        assert ser == orig.model_dump()


def test_serialize_response_non_model():
    data = "simple string"
    assert BaseRouter._serialize_response(data) == data


def test_put_route_decorator():
    router = BaseRouter()

    @router.put("/test_put", tags=["TestPut"], status_code=202)
    def put_endpoint(data: int):
        """Put endpoint doc."""
        return {"data": data}

    routes = router.get_routes()
    assert any(path == "/test_put" and method == "PUT" for path, method, _ in routes)
    meta = getattr(put_endpoint, "__route_meta__", {})
    assert meta.get("tags") == ["TestPut"]
    assert meta.get("status_code") == 202


def test_patch_route_decorator():
    router = BaseRouter()

    @router.patch("/test_patch", tags=["TestPatch"], status_code=203)
    def patch_endpoint(value: str):
        """Patch endpoint doc."""
        return {"value": value}

    routes = router.get_routes()
    assert any(
        path == "/test_patch" and method == "PATCH" for path, method, _ in routes
    )
    meta = getattr(patch_endpoint, "__route_meta__", {})
    assert meta.get("tags") == ["TestPatch"]
    assert meta.get("status_code") == 203


def test_delete_route_decorator():
    router = BaseRouter()

    @router.delete("/test_delete", status_code=204)
    def delete_endpoint():
        """Delete endpoint doc."""
        return {}

    routes = router.get_routes()
    assert any(
        path == "/test_delete" and method == "DELETE" for path, method, _ in routes
    )
    meta = getattr(delete_endpoint, "__route_meta__", {})
    assert meta.get("status_code") == 204


def test_build_parameters_and_body_query():
    def endpoint(id: int, a: int, b: str = "default"):
        return id, a, b

    router = BaseRouter()
    router.add_route("/query/{id}", "GET", endpoint)
    schema = router.generate_openapi()
    params = schema["paths"]["/query/{id}"]["get"].get("parameters", [])
    id_param = next((p for p in params if p["name"] == "id"), None)
    a_param = next((p for p in params if p["name"] == "a"), None)
    b_param = next((p for p in params if p["name"] == "b"), None)
    assert id_param is not None
    assert id_param["in"] == "path"
    assert (
        a_param is not None and a_param["in"] == "query" and a_param["required"] is True
    )
    assert (
        b_param is not None
        and b_param["in"] == "query"
        and b_param["required"] is False
    )


def test_build_parameters_and_body_request_body():
    class TestModel(BaseModel):
        field1: int
        field2: str

    def endpoint(model: TestModel):
        return model

    router = BaseRouter()
    router.add_route("/model", "POST", endpoint)
    schema = router.generate_openapi()
    op = schema["paths"]["/model"]["post"]
    assert "parameters" not in op or op["parameters"] == []
    assert "requestBody" in op
    req_body = op["requestBody"]
    ref = req_body["content"]["application/json"]["schema"]["$ref"]
    assert ref.endswith("/TestModel")


def test_build_responses_list_response_model():
    class TestModel(BaseModel):
        field: int

    router = BaseRouter()

    @router.get("/list", status_code=200, response_model=list[TestModel])
    def list_ep():
        return []

    schema = router.generate_openapi()
    responses = schema["paths"]["/list"]["get"]["responses"]
    resp_content = responses["200"]["content"]["application/json"]["schema"]
    assert resp_content["type"] == "array"
    assert resp_content["items"]["$ref"].endswith("/TestModel")


def test_build_responses_single_response_model():
    class TestModel(BaseModel):
        field: int

    router = BaseRouter()

    @router.get("/single", status_code=200, response_model=TestModel)
    def single_ep():
        return {}

    schema = router.generate_openapi()
    responses = schema["paths"]["/single"]["get"]["responses"]
    resp_content = responses["200"]["content"]["application/json"]["schema"]
    assert resp_content["$ref"].endswith("/TestModel")


def test_openapi_property_caching():
    router = BaseRouter(add_docs_route=False, add_openapi_route=False)
    router.add_route("/cache", "GET", lambda req: {"msg": "cache"})
    schema1 = router.openapi
    schema2 = router.openapi
    assert schema1 is schema2


def test_render_swagger_ui_html():
    url = "/test/openapi.json"
    html = BaseRouter.render_swagger_ui(url)
    assert "<html" in html
    assert "SwaggerUIBundle" in html
    assert url in html
    assert SWAGGER_URL.strip("/") in html


def test_register_docs_endpoints_not_implemented():
    class NotImplementedRouter(BaseRouter):
        pass

    with pytest.raises(NotImplementedError):
        NotImplementedRouter(app=object())


def test_build_parameters_and_body_no_annotation():
    router = DummyRouter(app=None)
    definitions = {}
    params, body = router._build_parameters_and_body(
        endpoint_no_annotation, definitions, "/test/{a}", "GET"
    )
    names = [p["name"] for p in params]
    assert "param" not in names
    assert any(p["name"] == "a" and p["in"] == "path" for p in params)
    assert body is None


def test_serialize_response_nested_dict():
    router = DummyRouter(app=None)
    m = DummyModel(field=123)
    dumped_m = m.model_dump()
    data = {"field": dumped_m, "list": [dumped_m, 456]}
    result = router._serialize_response(data)
    assert result == data


def test_include_router_with_none_prefix():
    main_router = BaseRouter()
    sub_router = BaseRouter()
    sub_router.add_route("/sub", "GET", lambda: "ok")
    main_router.include_router(sub_router, prefix=None)
    routes = main_router.get_routes()
    assert any(path == "/sub" for (path, _, _) in routes)


def test_get_model_schema_with_definitions(monkeypatch):
    class CustomModel(BaseModel):
        a: int

    def fake_schema(ref_template: str):
        return {
            "title": "CustomModel",
            "type": "object",
            "properties": {"a": {"type": "integer"}},
            "definitions": {"Extra": {"type": "string"}},
            "$defs": {"Another": {"type": "number"}},
        }

    monkeypatch.setattr(CustomModel, "model_json_schema", staticmethod(fake_schema))
    definitions = {}
    schema_ref = BaseRouter._get_model_schema(CustomModel, definitions)
    assert "Extra" in definitions
    assert "Another" in definitions
    assert "CustomModel" in definitions
    assert schema_ref == {"$ref": "#/components/schemas/CustomModel"}


def test_init_no_docs_endpoints():
    class TestRouter(BaseRouter):
        def __init__(self, *args, **kwargs):
            self.docs_called = False
            super().__init__(*args, **kwargs)

        def _register_docs_endpoints(self):
            self.docs_called = True

    router = TestRouter(app=object(), add_docs_route=False, add_openapi_route=False)
    assert not router.docs_called


def test_build_responses_invalid_response_model():
    router = BaseRouter()
    definitions = {}
    meta = {"response_model": int}
    responses = router._build_responses(meta, definitions, "200")
    assert "content" not in responses["200"]


def test_resolve_endpoint_params_missing_non_model():
    def func_no_anno(param):
        return param

    router = BaseRouter()
    with pytest.raises(ValueError) as excinfo:
        router.resolve_endpoint_params(func_no_anno, {}, {})
    assert "Missing required parameter" in str(excinfo.value)


def test_build_responses_list_invalid_inner():
    router = BaseRouter()
    definitions = {}
    meta = {"response_model": list[int]}
    responses = router._build_responses(meta, definitions, "200")
    assert "content" not in responses["200"]


def test_build_parameters_and_body_skips_unannotated_parameter():
    def endpoint(no_annotation, annotated: int):
        return no_annotation, annotated

    router = BaseRouter()
    definitions = {}

    parameters, request_body = router._build_parameters_and_body(
        endpoint, definitions, "/example/{annotated}", "GET"
    )

    parameter_names = [p["name"] for p in parameters]
    assert "no_annotation" not in parameter_names

    annotated_param = next((p for p in parameters if p["name"] == "annotated"), None)
    assert annotated_param is not None
    assert annotated_param["in"] == "path"
    assert request_body is None
