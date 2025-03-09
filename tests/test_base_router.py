import pytest

from fastopenapi.base_router import BaseRouter

from .conftest import Item, echo_int, return_item_model


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
    assert "Error casting parameter 'a' to <class 'int'>" in str(excinfo.value)

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


def test_render_swagger_ui_html():
    html = BaseRouter.render_swagger_ui("/test/openapi.json")
    assert (
        "<html" in html and "SwaggerUIBundle" in html and "/test/openapi.json" in html
    )
