from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel, computed_field

# Import the class under test
from fastopenapi.base_router import REDOC_URL, SWAGGER_URL, BaseRouter
from fastopenapi.error_handler import BadRequestError, ValidationError


class TestModel(BaseModel):
    name: str
    age: int
    is_active: bool = True

    @computed_field(alias="$active")
    def aliased_is_active(self) -> bool:
        return self.is_active


class ResponseModel(BaseModel):
    id: int
    message: str


class NestedModel(BaseModel):
    data: TestModel
    extra: str | None = None


class NestedListModel(BaseModel):
    data: list[TestModel]
    extra: str | None = None


class TestBaseRouter:
    def setup_method(self):
        self.app_mock = MagicMock()

        # Create router instance with overridden _register_docs_endpoints method
        class TestRouter(BaseRouter):
            def _register_docs_endpoints(self):
                pass

        self.router = TestRouter(
            app=self.app_mock,
            title="Test API",
            version="1.0.0",
            description="Test API Description",
        )

        self.router_no_app = TestRouter()

    def test_init(self):
        # Test that constructor properly initializes the object
        assert self.router.app == self.app_mock
        assert self.router.title == "Test API"
        assert self.router.version == "1.0.0"
        assert self.router.description == "Test API Description"
        assert self.router.docs_url == "/docs"
        assert self.router.redoc_url == "/redoc"
        assert self.router.openapi_url == "/openapi.json"
        assert self.router.openapi_version == "3.0.0"
        assert self.router._routes == []
        assert self.router._openapi_schema is None

    def test_init_without_app(self):
        assert self.router_no_app.app is None
        assert self.router_no_app.title == "My App"
        assert self.router_no_app.version == "0.1.0"
        assert self.router_no_app.description == "API documentation"
        assert self.router_no_app.docs_url == "/docs"
        assert self.router_no_app.redoc_url == "/redoc"
        assert self.router_no_app.openapi_url == "/openapi.json"
        assert self.router_no_app.openapi_version == "3.0.0"
        assert self.router_no_app._routes == []
        assert self.router_no_app._openapi_schema is None

    def test_add_route(self):
        # Test adding a route to the router
        def test_endpoint():
            pass

        self.router.add_route("/test", "GET", test_endpoint)
        assert len(self.router._routes) == 1
        assert self.router._routes[0] == ("/test", "GET", test_endpoint)

    def test_get_routes(self):
        # Test getting all routes
        def test_endpoint():
            pass

        self.router.add_route("/test1", "GET", test_endpoint)
        self.router.add_route("/test2", "POST", test_endpoint)

        routes = self.router.get_routes()
        assert len(routes) == 2
        assert routes[0] == ("/test1", "GET", test_endpoint)
        assert routes[1] == ("/test2", "POST", test_endpoint)

    def test_include_router(self):
        # Test including routes from another router
        def test_endpoint():
            pass

        # Create another router
        other_router = BaseRouter()
        other_router.add_route("/other", "GET", test_endpoint)

        # Include the other router with a prefix
        self.router.include_router(other_router, prefix="/api")
        assert len(self.router._routes) == 1
        assert self.router._routes[0] == ("/api/other", "GET", test_endpoint)

        # Include without prefix
        self.router.include_router(other_router)
        assert len(self.router._routes) == 2
        assert self.router._routes[1] == ("/other", "GET", test_endpoint)

    def test_http_method_decorators(self):
        # Test all HTTP method decorators

        @self.router.get("/get", tags=["test"])
        def get_endpoint():
            pass

        @self.router.post("/post")
        def post_endpoint():
            pass

        @self.router.put("/put")
        def put_endpoint():
            pass

        @self.router.patch("/patch")
        def patch_endpoint():
            pass

        @self.router.delete("/delete")
        def delete_endpoint():
            pass

        # Verify routes were added correctly
        routes = self.router.get_routes()
        assert len(routes) == 5

        methods = [route[1] for route in routes]
        paths = [route[0] for route in routes]

        assert "GET" in methods
        assert "POST" in methods
        assert "PUT" in methods
        assert "PATCH" in methods
        assert "DELETE" in methods

        assert "/get" in paths
        assert "/post" in paths
        assert "/put" in paths
        assert "/patch" in paths
        assert "/delete" in paths

        # Check that metadata was properly attached
        assert hasattr(get_endpoint, "__route_meta__")
        assert get_endpoint.__route_meta__["tags"] == ["test"]

    def test_generate_openapi_basic(self):
        # Test generating a basic OpenAPI schema

        @self.router.get("/test")
        def test_endpoint():
            """Test endpoint"""

        schema = self.router.generate_openapi()

        # Check basic structure
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
        assert "components" in schema

        # Check info section
        assert schema["info"]["title"] == "Test API"
        assert schema["info"]["version"] == "1.0.0"
        assert schema["info"]["description"] == "Test API Description"

        # Check paths
        assert "/test" in schema["paths"]
        assert "get" in schema["paths"]["/test"]
        assert "summary" in schema["paths"]["/test"]["get"]
        assert schema["paths"]["/test"]["get"]["summary"] == "Test endpoint"

    def test_generate_openapi_with_path_params(self):
        # Test OpenAPI generation with path parameters

        @self.router.get("/users/{user_id}")
        def get_user(user_id: int):
            pass

        schema = self.router.generate_openapi()

        # Path should be converted to OpenAPI format
        assert "/users/{user_id}" in schema["paths"]

        # Check parameters
        parameters = schema["paths"]["/users/{user_id}"]["get"]["parameters"]
        assert len(parameters) == 1
        assert parameters[0]["name"] == "user_id"
        assert parameters[0]["in"] == "path"
        assert parameters[0]["required"] is True
        assert parameters[0]["schema"]["type"] == "integer"

    def test_generate_openapi_with_query_params(self):
        # Test OpenAPI generation with query parameters

        @self.router.get("/search")
        def search(q: str, limit: int = 10):
            pass

        schema = self.router.generate_openapi()

        # Check parameters
        parameters = schema["paths"]["/search"]["get"]["parameters"]
        assert len(parameters) == 2

        # First parameter (required)
        q_param = next(p for p in parameters if p["name"] == "q")
        assert q_param["in"] == "query"
        assert q_param["required"] is True
        assert q_param["schema"]["type"] == "string"

        # Second parameter (with default)
        limit_param = next(p for p in parameters if p["name"] == "limit")
        assert limit_param["in"] == "query"
        assert limit_param["required"] is False
        assert limit_param["schema"]["type"] == "integer"

    def test_generate_openapi_with_request_body(self):
        # Test OpenAPI generation with request body (Pydantic model)

        @self.router.post("/users")
        def create_user(user: TestModel):
            pass

        schema = self.router.generate_openapi()

        # Check request body
        request_body = schema["paths"]["/users"]["post"]["requestBody"]
        assert request_body["required"] is True
        assert "application/json" in request_body["content"]
        assert "$ref" in request_body["content"]["application/json"]["schema"]

        # Check that model schema is in components
        ref = request_body["content"]["application/json"]["schema"]["$ref"]
        assert ref == "#/components/schemas/TestModel"
        assert "TestModel" in schema["components"]["schemas"]

    def test_generate_openapi_with_response_error(self):
        # Test OpenAPI generation with response error

        @self.router.post("/users", response_errors=[400, 404, 500], response_model=int)
        def create_user(user: TestModel):
            return 1

        schema = self.router.generate_openapi()

        # Check response
        response = schema["paths"]["/users"]["post"]["responses"]["200"]
        assert "content" in response
        assert "application/json" in response["content"]

        responses = schema["paths"]["/users"]["post"]["responses"]
        assert "200" in responses
        assert "400" in responses
        assert "404" in responses
        assert "500" in responses

        assert "ErrorSchema" in schema["components"]["schemas"]

    def test_generate_openapi_with_incorrect_response_model(self):
        # Test OpenAPI generation with incorrect response model

        @self.router.post("/users", response_model=tuple)
        def create_user(user: TestModel):
            return (1, 2)

        with pytest.raises(Exception, match="Incorrect response_model"):
            self.router.generate_openapi()

    def test_generate_openapi_with_incorrect_list_response_model(self):
        # Test OpenAPI generation with incorrect response model

        @self.router.post("/users", response_model=list[tuple])
        def create_user(user: TestModel):
            return [(1, 2)]

        with pytest.raises(Exception, match="Incorrect response_model"):
            self.router.generate_openapi()

    def test_generate_openapi_with_simple_type_as_response_model(self):
        # Test OpenAPI generation with python type as response model

        @self.router.post("/users", response_model=int)
        def create_user(user: TestModel):
            return 1

        schema = self.router.generate_openapi()

        # Check response
        response = schema["paths"]["/users"]["post"]["responses"]["200"]
        assert "content" in response
        assert "application/json" in response["content"]

        resp_type = response["content"]["application/json"]["schema"]["type"]
        assert "integer" == resp_type

    def test_generate_openapi_with_response_model(self):
        # Test OpenAPI generation with response model

        @self.router.post("/users", response_model=list[ResponseModel])
        def create_user(user: TestModel):
            pass

        schema = self.router.generate_openapi()

        # Check response
        response = schema["paths"]["/users"]["post"]["responses"]["200"]
        assert "content" in response
        assert "application/json" in response["content"]
        assert "$ref" in response["content"]["application/json"]["schema"]["items"]

        # Check that response model schema is in components
        ref = response["content"]["application/json"]["schema"]["items"]["$ref"]
        assert ref == "#/components/schemas/ResponseModel"
        assert "ResponseModel" in schema["components"]["schemas"]

    def test_generate_openapi_with_nested_list_response_model(self):
        # Test OpenAPI generation with response model with nested model list

        @self.router.post("/users", response_model=NestedListModel)
        def create_user(user: TestModel):
            pass

        schema = self.router.generate_openapi()

        # Check response
        response = schema["paths"]["/users"]["post"]["responses"]["200"]
        assert "content" in response
        assert "application/json" in response["content"]
        assert "$ref" in response["content"]["application/json"]["schema"]

        # Check that response model schema is in components
        ref = response["content"]["application/json"]["schema"]["$ref"]
        schemas = schema["components"]["schemas"]
        assert ref == "#/components/schemas/NestedListModel"
        assert "NestedListModel" in schemas
        assert "TestModel" in schemas

        # Check that TestModel inside NestedModel
        ref = schemas["NestedListModel"]["properties"]["data"]["items"]["$ref"]
        assert ref == "#/components/schemas/TestModel"

    def test_generate_openapi_with_list_response(self):
        # Test OpenAPI generation with List response model

        @self.router.get("/users", response_model=list[ResponseModel])
        def list_users():
            pass

        schema = self.router.generate_openapi()

        # Check response
        response = schema["paths"]["/users"]["get"]["responses"]["200"]
        assert "content" in response
        assert "application/json" in response["content"]

        # Check array schema
        array_schema = response["content"]["application/json"]["schema"]
        assert array_schema["type"] == "array"
        assert "$ref" in array_schema["items"]
        assert array_schema["items"]["$ref"] == "#/components/schemas/ResponseModel"

    def test_generate_openapi_with_status_code(self):
        # Test OpenAPI generation with custom status code

        @self.router.post("/users", status_code=201)
        def create_user():
            pass

        schema = self.router.generate_openapi()

        # Check response has correct status code
        assert "201" in schema["paths"]["/users"]["post"]["responses"]
        assert "description" in schema["paths"]["/users"]["post"]["responses"]["201"]
        assert (
            schema["paths"]["/users"]["post"]["responses"]["201"]["description"]
            == "Created"
        )

    def test_openapi_property(self):
        # Test the openapi property (cached schema)

        @self.router.get("/test")
        def test_endpoint():
            pass

        # First call should generate the schema
        schema1 = self.router.openapi

        # Add new route
        @self.router.post("/new")
        def new_endpoint():
            pass

        # Second call should return cached schema (without the new route)
        schema2 = self.router.openapi

        assert schema1 is schema2
        assert "/new" not in schema1["paths"]

    def test_serialize_response_with_pydantic_model(self):
        # Test serializing a Pydantic model response
        model = ResponseModel(id=1, message="test")
        result = BaseRouter()._serialize_response(model)

        assert isinstance(result, dict)
        assert result["id"] == 1
        assert result["message"] == "test"

    def test_serialize_response_with_list(self):
        # Test serializing a list of Pydantic models
        models = [
            ResponseModel(id=1, message="test1"),
            ResponseModel(id=2, message="test2"),
        ]
        result = BaseRouter()._serialize_response(models)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["id"] == 2

    def test_serialize_response_with_dict(self):
        # Test serializing a dict with Pydantic model values
        data = {
            "item1": ResponseModel(id=1, message="test1"),
            "item2": ResponseModel(id=2, message="test2"),
        }
        result = BaseRouter()._serialize_response(data)

        assert isinstance(result, dict)
        assert len(result) == 2
        assert result["item1"]["id"] == 1
        assert result["item2"]["id"] == 2

    def test_serialize_response_with_primitive(self):
        # Test serializing primitive values
        router = BaseRouter()
        assert router._serialize_response(5) == 5
        assert router._serialize_response("test") == "test"
        assert router._serialize_response(True) is True

    def test_get_model_schema(self):
        # Test getting Pydantic model schema
        definitions = {}
        schema = BaseRouter()._get_model_schema(TestModel, definitions)

        assert "$ref" in schema
        assert schema["$ref"] == "#/components/schemas/TestModel"
        assert "TestModel" in definitions
        assert definitions["TestModel"]["properties"]["name"]["type"] == "string"
        assert definitions["TestModel"]["properties"]["age"]["type"] == "integer"
        assert definitions["TestModel"]["properties"]["$active"]["type"] == "boolean"

    def test_get_model_schema_with_nested_models(self):
        # Test getting schema for models with nested models
        definitions = {}
        schema = BaseRouter()._get_model_schema(NestedModel, definitions)

        assert "$ref" in schema
        assert schema["$ref"] == "#/components/schemas/NestedModel"
        assert "NestedModel" in definitions
        assert "TestModel" in definitions  # Nested model should be in definitions too

    def test_render_swagger_ui(self):
        # Test rendering Swagger UI HTML
        html = BaseRouter.render_swagger_ui("/api/openapi.json")

        assert "<!DOCTYPE html>" in html
        assert SWAGGER_URL in html
        assert "url: '/api/openapi.json'" in html
        assert "dom_id: '#swagger-ui'" in html

    def test_render_redoc_ui(self):
        # Test rendering ReDoc UI HTML
        html = BaseRouter.render_redoc_ui("/api/openapi.json")

        assert "<!DOCTYPE html>" in html
        assert REDOC_URL in html
        assert "spec-url='/api/openapi.json'" in html

    def test_resolve_endpoint_params_with_primitive_types(self):
        # Test resolving endpoint parameters with primitive types
        def endpoint(name: str, age: int, active: bool = False):
            return {"name": name, "age": age, "active": active}

        params = {"name": "John", "age": "30"}
        result = BaseRouter.resolve_endpoint_params(endpoint, params, {})

        assert result["name"] == "John"
        assert result["age"] == 30
        assert result["active"] is False

    def test_resolve_endpoint_params_with_pydantic_model(self):
        # Test resolving endpoint parameters with Pydantic model
        def endpoint(user: TestModel):
            return user

        body = {"name": "John", "age": 30}
        result = BaseRouter.resolve_endpoint_params(endpoint, {}, body)

        assert isinstance(result["user"], TestModel)
        assert result["user"].name == "John"
        assert result["user"].age == 30
        assert result["user"].is_active is True  # Default value
        assert result["user"].aliased_is_active is True

    def test_resolve_endpoint_params_missing_required(self):
        # Test error when required parameter is missing
        def endpoint(name: str, age: int):
            pass

        params = {"name": "John"}

        with pytest.raises(BadRequestError) as excinfo:
            BaseRouter.resolve_endpoint_params(endpoint, params, {})

        assert "Missing required parameter" in str(excinfo.value)
        assert "age" in str(excinfo.value)

    def test_resolve_endpoint_params_invalid_type(self):
        # Test error when parameter type is invalid
        def endpoint(age: int):
            pass

        params = {"age": "not_an_integer"}

        with pytest.raises(BadRequestError) as excinfo:
            BaseRouter.resolve_endpoint_params(endpoint, params, {})

        assert "Error parsing parameter" in str(excinfo.value)

    def test_resolve_endpoint_params_model_validation_error(self):
        # Test error when model validation fails
        def endpoint(user: TestModel):
            pass

        body = {"name": "John"}  # Missing required 'age' field

        with pytest.raises(ValidationError) as excinfo:
            BaseRouter.resolve_endpoint_params(endpoint, {}, body)

        assert "Validation error for parameter" in str(excinfo.value)

    def test_build_parameters_for_get_with_model(self):
        # Test building parameters for GET with Pydantic model
        def endpoint(query: TestModel):
            pass

        definitions = {}
        params, body = self.router._build_parameters_and_body(
            endpoint, definitions, "/test", "GET"
        )

        # Should convert model to query parameters
        assert len(params) == 4
        assert params[0]["in"] == "query"
        assert params[1]["in"] == "query"
        assert params[2]["in"] == "query"
        assert params[3]["in"] == "query"

        names = [p["name"] for p in params]
        assert "name" in names
        assert "age" in names
        assert "is_active" in names
        assert "$active" in names  # alias

        # No request body for GET
        assert body is None

    def test_register_docs_endpoints_not_implemented(self):
        # Test that base class raises NotImplementedError
        router = BaseRouter()

        with pytest.raises(NotImplementedError):
            router._register_docs_endpoints()

    def test_resolve_pydantic_model(self):
        """Test resolving parameters for a Pydantic model."""
        # Successful case
        params = {"name": "John", "age": "30"}
        result = BaseRouter._resolve_pydantic_model(TestModel, params, "user")
        assert isinstance(result, TestModel)
        assert result.name == "John"
        assert result.age == 30

        # Test with list field as string (conversion to list)
        class ModelWithList(BaseModel):
            tags: list[str]
            name: str

        params = {"tags": "python", "name": "John"}
        result = BaseRouter._resolve_pydantic_model(ModelWithList, params, "model")
        assert isinstance(result, ModelWithList)
        assert result.tags == ["python"]

        # Error case
        with pytest.raises(ValidationError) as excinfo:
            BaseRouter._resolve_pydantic_model(TestModel, {"name": "John"}, "user")
        assert "Validation error for parameter 'user'" in str(excinfo.value)

    def test_build_array_schema(self):
        """Test building OpenAPI schema for array types."""
        # Test with typed list
        schema = self.router._build_array_schema(list[int])
        assert schema["type"] == "array"
        assert schema["items"]["type"] == "integer"

        # Test with string list
        schema = self.router._build_array_schema(list[str])
        assert schema["type"] == "array"
        assert schema["items"]["type"] == "string"

        # Test with untyped list
        schema = self.router._build_array_schema(list)
        assert schema["type"] == "array"
        assert schema["items"]["type"] == "string"  # Default type

    def test_resolve_endpoint_params_with_list(self):
        """Test resolving endpoint params with list type."""

        # Define endpoint with list parameter
        def endpoint(tags: list[str]):
            return tags

        # Test with string value that should be converted to list
        params = {"tags": ["python"]}
        result = BaseRouter.resolve_endpoint_params(endpoint, params, {})
        assert result["tags"] == ["python"]

        # Test with already list value
        params = {"tags": ["python", "fastapi"]}
        result = BaseRouter.resolve_endpoint_params(endpoint, params, {})
        assert result["tags"] == ["python", "fastapi"]

    def test_build_parameter_schema(self):
        """Test the _build_parameter_schema method.
        This targets both branches - list type and non-list type."""

        # Test with a list type - should call _build_array_schema
        list_schema = self.router._build_parameter_schema(list[str])
        assert list_schema["type"] == "array"
        assert list_schema["items"]["type"] == "string"

        # Test with a typing.List type - should also call _build_array_schema
        typing_list_schema = self.router._build_parameter_schema(list[int])
        assert typing_list_schema["type"] == "array"
        assert typing_list_schema["items"]["type"] == "integer"

        # Test with non-list type, which is in PYTHON_TYPE_MAPPING
        int_schema = self.router._build_parameter_schema(int)
        assert int_schema["type"] == "integer"

        # Test with non-list type, not in PYTHON_TYPE_MAPPING (should default to string)
        class CustomType:
            pass

        custom_schema = self.router._build_parameter_schema(CustomType)
        assert custom_schema["type"] == "string"

    def test_resolve_pydantic_model_no_model_fields(self):
        """
        Test the branch in _resolve_pydantic_model where
        hasattr(model_class, "model_fields") is False
        """

        class FakeModel:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)

        assert not hasattr(FakeModel, "model_fields")

        params = {"name": "test", "value": 42}
        result = BaseRouter._resolve_pydantic_model(FakeModel, params, "fake_model")

        assert isinstance(result, FakeModel)
        assert result.name == "test"
        assert result.value == 42

    def test_handle_validation_error_no_errors(self):
        """Test _handle_validation_error when error.errors() returns an empty list"""
        # Create a mock PydanticValidationError that returns an empty errors list
        from unittest.mock import MagicMock

        mock_error = MagicMock()
        mock_error.errors.return_value = (
            []
        )  # Empty list will make 'if errors:' evaluate to False
        # String representation of the error for the error message
        mock_error.__str__.return_value = "Empty validation error"

        param_types = {"name": str, "age": int}

        # Call the method and expect a BadRequestError
        error = BaseRouter._handle_validation_error(mock_error, param_types)

        # Check that we got the generic error message (else branch after 'if errors:')
        assert isinstance(error, BadRequestError)
        assert "Parameter validation failed" in error.message
        assert "Empty validation error" in error.details

    def test_handle_validation_error_empty_loc(self):
        """Test _handle_validation_error when 'loc' is empty"""

        mock_error = MagicMock()
        mock_error.errors.return_value = [
            {"msg": "validation error message", "loc": []}  # Empty loc list
        ]
        mock_error.__str__.return_value = "Error with empty location"

        param_types = {"name": str, "age": int}

        error = BaseRouter._handle_validation_error(mock_error, param_types)

        assert isinstance(error, BadRequestError)
        assert "Parameter validation failed" in error.message
        assert "Error with empty location" in error.details

    def test_handle_validation_error_param_not_in_types(self):
        """Test _handle_validation_error when parameter is not in param_types"""
        from unittest.mock import MagicMock

        mock_error = MagicMock()
        mock_error.errors.return_value = [
            {"loc": ["unknown_param"], "msg": "validation error message"}
        ]
        mock_error.__str__.return_value = "Error with unknown parameter"

        param_types = {}

        error = BaseRouter._handle_validation_error(mock_error, param_types)

        assert isinstance(error, BadRequestError)
        assert "Parameter validation failed" in error.message
        assert "Error with unknown parameter" in error.details
