import inspect
import threading
from typing import Any, Optional, Union
from unittest.mock import Mock, patch

from pydantic import BaseModel, Field

from fastopenapi.core.constants import SecuritySchemeType
from fastopenapi.core.params import Body, Depends, File, Form, Header, Query, Security
from fastopenapi.core.router import BaseRouter
from fastopenapi.openapi.generator import (
    OpenAPIGenerator,
    ParameterInfo,
    ParameterProcessor,
    ResponseBuilder,
    SchemaBuilder,
)


class NestedModel(BaseModel):
    nested_field: str
    count: int = Field(gt=0, description="Count must be positive")


class ComplexModel(BaseModel):
    name: str = Field(min_length=1, max_length=100, description="User name")
    age: int = Field(ge=0, le=150, description="User age")
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    nested: NestedModel | None = None
    is_verified: bool = Field(default=False, alias="verified")


class SimpleModel(BaseModel):
    name: str = Field(min_length=1, max_length=50, description="User name")
    age: int = Field(ge=0, le=150, description="User age")
    tags: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    price: float = Query(gt=0.0, multiple_of=0.01, description="Price", examples=[0.5])


class TestOpenAPIGenerator:
    def setup_method(self):
        self.router = BaseRouter(
            title="Test API",
            version="1.0.0",
            description="Test API Description",
            security_scheme=SecuritySchemeType.BEARER_JWT,
        )
        self.generator = OpenAPIGenerator(self.router)

    def test_parameter_with_constraints(self):
        """Test parameters with validation constraints"""

        @self.router.get("/items")
        def get_items(
            name: str = Query(min_length=2, max_length=50, pattern=r"^[a-zA-Z]+$"),
            age: int = Query(ge=18, le=100, description="User age"),
            price: float = Query(gt=0.0, multiple_of=0.01),
            tags: list[str] = Query(default=[]),
        ):
            pass

        schema = self.generator.generate()
        params = schema["paths"]["/items"]["get"]["parameters"]

        # Find specific parameters
        name_param = next(p for p in params if p["name"] == "name")
        age_param = next(p for p in params if p["name"] == "age")
        price_param = next(p for p in params if p["name"] == "price")
        tags_param = next(p for p in params if p["name"] == "tags")

        # Check constraints are applied
        assert name_param["schema"]["minLength"] == 2
        assert name_param["schema"]["maxLength"] == 50
        assert name_param["schema"]["pattern"] == r"^[a-zA-Z]+$"

        assert age_param["schema"]["minimum"] == 18
        assert age_param["schema"]["maximum"] == 100
        assert age_param["description"] == "User age"

        assert price_param["schema"]["exclusiveMinimum"] == 0.0
        assert price_param["schema"]["multipleOf"] == 0.01

        assert tags_param["schema"]["type"] == "array"
        assert tags_param["schema"]["items"]["type"] == "string"

    def test_parameter_with_examples(self):
        """Test parameters with examples"""

        @self.router.get("/search")
        def search(
            q: str = Query(examples=["python", "fastapi", "web"]),
            category: str = Query(examples=["tech", "science"]),
        ):
            pass

        schema = self.generator.generate()
        params = schema["paths"]["/search"]["get"]["parameters"]

        q_param = next(p for p in params if p["name"] == "q")
        assert "examples" in q_param
        assert len(q_param["examples"]) == 3

    def test_header_parameter_with_conversion(self):
        """Test header parameter with underscore conversion"""

        @self.router.get("/api")
        def api_endpoint(
            content_type: str = Header(),
            user_agent: str = Header(convert_underscores=False),
            custom_header: str = Header(alias="X-Custom-Header"),
        ):
            pass

        schema = self.generator.generate()
        params = schema["paths"]["/api"]["get"]["parameters"]

        # Check header name conversion
        content_type_param = next(p for p in params if p["name"] == "content-type")
        user_agent_param = next(p for p in params if p["name"] == "user_agent")
        custom_param = next(p for p in params if p["name"] == "X-Custom-Header")

        assert content_type_param["in"] == "header"
        assert user_agent_param["in"] == "header"
        assert custom_param["in"] == "header"

    def test_body_parameter_with_embed(self):
        """Test Body parameter with embed option"""

        @self.router.post("/data")
        def post_data(data: str = Body(embed=True, media_type="text/plain")):
            pass

        schema = self.generator.generate()
        request_body = schema["paths"]["/data"]["post"]["requestBody"]

        assert "text/plain" in request_body["content"]
        assert request_body["content"]["text/plain"]["schema"]["type"] == "string"

    def test_form_and_file_parameters(self):
        """Test Form and File parameters"""

        @self.router.post("/upload")
        def upload_file(
            title: str = Form(),
            description: str = Form(min_length=10),
            file: bytes = File(),
            optional_file: bytes | None = File(default=None),
        ):
            pass

        schema = self.generator.generate()
        request_body = schema["paths"]["/upload"]["post"]["requestBody"]

        assert "multipart/form-data" in request_body["content"]
        properties = request_body["content"]["multipart/form-data"]["schema"][
            "properties"
        ]

        assert "title" in properties
        assert "description" in properties
        assert "file" in properties
        assert "optional_file" in properties

        # File should have binary format
        assert properties["file"]["type"] == "string"
        assert properties["file"]["format"] == "binary"

    def test_mixed_form_and_multipart(self):
        """Test mixing form data and files"""

        @self.router.post("/mixed")
        def mixed_upload(name: str = Form(), file: bytes = File()):
            pass

        schema = self.generator.generate()
        request_body = schema["paths"]["/mixed"]["post"]["requestBody"]

        # Should use multipart when files are present
        assert "multipart/form-data" in request_body["content"]

    def test_security_dependency(self):
        """Test Security dependency handling"""

        def get_current_user(token: str = Depends()) -> dict:
            return {"user": "test"}

        @self.router.get("/protected")
        def protected_endpoint(
            user: dict = Security(get_current_user, scopes=["read", "write"])
        ):
            pass

        schema = self.generator.generate()

        # Should have security scheme
        assert "components" in schema
        assert "securitySchemes" in schema["components"]

        # Should auto-add security to operation
        operation = schema["paths"]["/protected"]["get"]
        assert "security" in operation
        assert len(operation["security"]) == 1

    def test_depends_parameter(self):
        """Test Depends parameter (should be skipped)"""

        def get_db():
            return "db"

        @self.router.get("/items")
        def get_items(db: str = Depends(get_db), limit: int = Query(default=10)):
            pass

        schema = self.generator.generate()
        params = schema["paths"]["/items"]["get"]["parameters"]

        # Only limit should be present, db should be skipped
        assert len(params) == 1
        assert params[0]["name"] == "limit"

    def test_list_response_model(self):
        """Test List response model handling"""

        @self.router.get("/users", response_model=list[ComplexModel])
        def list_users():
            pass

        schema = self.generator.generate()
        response = schema["paths"]["/users"]["get"]["responses"]["200"]

        assert response["content"]["application/json"]["schema"]["type"] == "array"
        assert "$ref" in response["content"]["application/json"]["schema"]["items"]

    def test_custom_error_responses(self):
        """Test custom error responses"""

        @self.router.post("/items", response_errors=[400, 422, 500])
        def create_item(item: ComplexModel):
            pass

        schema = self.generator.generate()
        responses = schema["paths"]["/items"]["post"]["responses"]

        assert "400" in responses
        assert "422" in responses
        assert "500" in responses

        # All should reference ErrorSchema
        for code in ["400", "422", "500"]:
            error_content = responses[code]["content"]["application/json"]["schema"]
            assert error_content["$ref"] == "#/components/schemas/ErrorSchema"

    def test_nested_model_definitions(self):
        """Test nested model schema handling"""

        @self.router.post("/complex")
        def create_complex(data: ComplexModel):
            pass

        schema = self.generator.generate()

        # Should have both models in definitions
        assert "ComplexModel" in schema["components"]["schemas"]
        assert "NestedModel" in schema["components"]["schemas"]

    def test_model_with_alias(self):
        """Test model with field aliases"""

        @self.router.post("/aliased")
        def create_aliased(data: ComplexModel):
            pass

        schema = self.generator.generate()
        complex_schema = schema["components"]["schemas"]["ComplexModel"]

        # Should have alias in properties
        assert "verified" in complex_schema["properties"]

    def test_path_parameter_conversion(self):
        """Test path parameter format conversion"""

        @self.router.get("/items/<int:item_id>/details/<slug>")
        def get_item_details(item_id: int, slug: str):
            pass

        schema = self.generator.generate()

        # Should convert to OpenAPI format
        assert "/items/{item_id}/details/{slug}" in schema["paths"]

    def test_no_request_body_for_get(self):
        """Test that GET with model creates query params"""

        @self.router.get("/search")
        def search_complex(filters: ComplexModel):
            pass

        schema = self.generator.generate()
        operation = schema["paths"]["/search"]["get"]

        # Should have parameters, not requestBody
        assert "parameters" in operation
        assert "requestBody" not in operation

        # Should have multiple query parameters from model fields
        params = operation["parameters"]
        param_names = [p["name"] for p in params]
        assert "name" in param_names
        assert "age" in param_names
        assert "verified" in param_names  # alias

    def test_empty_response_for_204(self):
        """Test 204 No Content response"""

        @self.router.delete("/items/{item_id}", status_code=204)
        def delete_item(item_id: int):
            pass

        schema = self.generator.generate()
        response = schema["paths"]["/items/{item_id}"]["delete"]["responses"]["204"]

        assert response["description"] == "No Content"

    def test_deprecated_parameter(self):
        """Test deprecated parameter"""

        @self.router.get("/legacy")
        def legacy_endpoint(old_param: str = Query(deprecated=True)):
            pass

        schema = self.generator.generate()
        params = schema["paths"]["/legacy"]["get"]["parameters"]

        assert params[0]["deprecated"] is True

    def test_include_in_schema_false(self):
        """Test parameter with include_in_schema=False"""

        @self.router.get("/hidden")
        def hidden_param_endpoint(
            visible: str = Query(), hidden: str = Query(include_in_schema=False)
        ):
            pass

        schema = self.generator.generate()
        params = schema["paths"]["/hidden"]["get"]["parameters"]

        # Only visible parameter should be included
        assert len(params) == 1
        assert params[0]["name"] == "visible"

    def test_operation_id_generation(self):
        """Test operation ID generation"""

        @self.router.get("/test")
        def test_endpoint():
            pass

        schema = self.generator.generate()
        operation = schema["paths"]["/test"]["get"]

        assert operation["operationId"] == "get_test_endpoint"

    def test_response_model_with_description(self):
        """Test response model with custom description"""

        @self.router.get(
            "/described", response_model=ComplexModel, description="Custom description"
        )
        def described_endpoint():
            pass

        schema = self.generator.generate()
        operation = schema["paths"]["/described"]["get"]

        assert operation["description"] == "Custom description"

    def test_schema_builder_array_type(self):
        """Test SchemaBuilder array type handling"""
        builder = SchemaBuilder({}, self.generator._cache_lock)

        # Test list annotation
        schema = builder.build_parameter_schema(list[str])
        assert schema["type"] == "array"
        assert schema["items"]["type"] == "string"

    def test_schema_builder_union_type(self):
        """Test SchemaBuilder union type handling"""
        builder = SchemaBuilder({}, self.generator._cache_lock)

        # Test Optional type
        schema = builder.build_parameter_schema(Optional[int])
        assert schema["type"] == "integer"
        assert schema["nullable"] is True

    def test_parameter_with_default_value(self):
        """Test parameter with serializable default value"""

        @self.router.get("/defaults")
        def defaults_endpoint(
            count: int = Query(default=10),
            active: bool = Query(default=True),
            name: str = Query(default="test"),
        ):
            pass

        schema = self.generator.generate()
        params = schema["paths"]["/defaults"]["get"]["parameters"]

        count_param = next(p for p in params if p["name"] == "count")
        active_param = next(p for p in params if p["name"] == "active")
        name_param = next(p for p in params if p["name"] == "name")

        assert count_param["schema"]["default"] == 10
        assert active_param["schema"]["default"] is True
        assert name_param["schema"]["default"] == "test"

    def test_model_schema_caching(self):
        """Test model schema caching"""
        builder = SchemaBuilder({}, self.generator._cache_lock)

        # First call should cache
        schema1 = builder.get_model_schema(ComplexModel)
        schema2 = builder.get_model_schema(ComplexModel)

        # Should return same reference
        assert schema1 == schema2
        assert "ComplexModel" in builder.definitions

    def test_response_builder_error_responses(self):
        """Test ResponseBuilder error response generation"""
        route = Mock()
        route.meta = {"security": True}

        builder = ResponseBuilder(self.generator.schema_builder)
        responses = builder.build_responses(route)

        # Should add security error responses
        assert "401" in responses
        assert "403" in responses

    def test_response_with_no_model(self):
        """Test response without model"""

        @self.router.get("/simple")
        def simple_endpoint():
            return {"message": "ok"}

        schema = self.generator.generate()
        response = schema["paths"]["/simple"]["get"]["responses"]["200"]

        assert response["description"] == "OK"
        assert "content" not in response

    def test_authorization_header_skipped(self):
        """Test that Authorization header is skipped"""

        @self.router.get("/auth")
        def auth_endpoint(
            authorization: str = Header(alias="Authorization"),
            other_header: str = Header(convert_underscores=False),
        ):
            pass

        schema = self.generator.generate()
        params = schema["paths"]["/auth"]["get"]["parameters"]

        # Should only have other_header, Authorization should be skipped
        assert len(params) == 1
        assert params[0]["name"] == "other_header"

    def test_invalid_default_value_handling(self):
        """Test handling of non-serializable default values"""

        class NonSerializable:
            pass

        @self.router.get("/invalid")
        def invalid_endpoint(obj: str = Query(default=NonSerializable())):
            pass

        # Should not raise exception, just skip the default
        schema = self.generator.generate()
        params = schema["paths"]["/invalid"]["get"]["parameters"]
        assert "default" not in params[0]["schema"]

    def test_complex_nested_schema(self):
        """Test complex nested schema with definitions"""

        class Level3(BaseModel):
            value: str

        class Level2(BaseModel):
            level3: Level3
            items: list[Level3]

        class Level1(BaseModel):
            level2: Level2
            optional_level2: Level2 | None = None

        @self.router.post("/nested")
        def nested_endpoint(data: Level1):
            pass

        schema = self.generator.generate()

        # All levels should be in definitions
        assert "Level1" in schema["components"]["schemas"]
        assert "Level2" in schema["components"]["schemas"]
        assert "Level3" in schema["components"]["schemas"]

    def test_error_schema_generation(self):
        """Test error schema is properly generated"""
        schema = self.generator.generate()

        assert "ErrorSchema" in schema["components"]["schemas"]
        error_schema = schema["components"]["schemas"]["ErrorSchema"]

        assert error_schema["type"] == "object"
        assert "error" in error_schema["properties"]
        assert "type" in error_schema["properties"]["error"]["properties"]
        assert "message" in error_schema["properties"]["error"]["properties"]
        assert "status" in error_schema["properties"]["error"]["properties"]

    def test_pagination_params_schema(self):
        """Test pagination parameters schema"""
        schema = self.generator.generate()

        assert "PaginationParams" in schema["components"]["schemas"]
        pagination_schema = schema["components"]["schemas"]["PaginationParams"]

        assert "page" in pagination_schema["properties"]
        assert "limit" in pagination_schema["properties"]
        assert pagination_schema["properties"]["page"]["minimum"] == 1
        assert pagination_schema["properties"]["limit"]["maximum"] == 100

    def test_schema_builder_init(self):
        """Test SchemaBuilder initialization"""
        definitions = {}
        lock = threading.Lock()
        builder = SchemaBuilder(definitions, lock)

        assert builder.definitions is definitions
        assert builder._cache_lock is lock
        assert builder._model_schema_cache == {}

    def test_schema_builder_build_parameter_schema_basic_types(self):
        """Test building schema for basic Python types"""
        builder = SchemaBuilder({}, threading.Lock())

        assert builder.build_parameter_schema(int) == {"type": "integer"}
        assert builder.build_parameter_schema(float) == {"type": "number"}
        assert builder.build_parameter_schema(bool) == {"type": "boolean"}
        assert builder.build_parameter_schema(str) == {"type": "string"}

    def test_schema_builder_build_parameter_schema_unknown_type(self):
        """Test building schema for unknown type defaults to string"""
        builder = SchemaBuilder({}, threading.Lock())

        class CustomType:
            pass

        assert builder.build_parameter_schema(CustomType) == {"type": "string"}

    def test_schema_builder_build_array_schema_without_args(self):
        """Test building array schema without type arguments"""
        builder = SchemaBuilder({}, threading.Lock())

        with patch("typing.get_args", return_value=[]):
            schema = builder._build_array_schema(list)
            assert schema == {"type": "array", "items": {"type": "string"}}

    def test_schema_builder_build_union_schema_non_optional(self):
        """Test building schema for non-Optional Union types"""
        builder = SchemaBuilder({}, threading.Lock())

        schema = builder._build_union_schema(Union[str, int])
        assert schema == {"type": "string"}

    def test_schema_builder_build_union_schema_empty(self):
        """Test building schema for empty"""
        builder = SchemaBuilder({}, threading.Lock())

        schema = builder._build_union_schema(Union[None])
        assert schema == {"type": "string"}

    def test_schema_builder_build_parameter_schema_from_param_basic(self):
        """Test building schema from Param object"""
        builder = SchemaBuilder({}, threading.Lock())

        param = Mock()
        param.annotation = str
        param.default = Query()

        schema = builder.build_parameter_schema_from_param(param)
        assert "type" in schema

    def test_schema_builder_build_parameter_schema_from_non_param(self):
        """Test building schema from Param object"""
        builder = SchemaBuilder({}, threading.Lock())

        param = Mock()
        param.annotation = str
        param.default = Mock()

        schema = builder.build_parameter_schema_from_param(param)
        assert "type" in schema

    def test_schema_builder_apply_metadata_constraints_with_constraints(self):
        """Test applying metadata constraints"""
        builder = SchemaBuilder({}, threading.Lock())
        schema = {}

        # Mock constraint objects
        min_len_constraint = Mock()
        min_len_constraint.__class__.__name__ = "MinLen"
        min_len_constraint.min_length = 5

        max_len_constraint = Mock()
        max_len_constraint.__class__.__name__ = "MaxLen"
        max_len_constraint.max_length = 100

        ge_constraint = Mock()
        ge_constraint.__class__.__name__ = "Ge"
        ge_constraint.ge = 0

        pattern_constraint = Mock()
        pattern_constraint.__class__.__name__ = "_PydanticGeneralMetadata"
        pattern_constraint.pattern = r"^[a-z]+$"

        param_obj = Mock()
        param_obj.metadata = [
            min_len_constraint,
            max_len_constraint,
            ge_constraint,
            pattern_constraint,
        ]

        builder._apply_metadata_constraints(schema, param_obj)

        assert schema["minLength"] == 5
        assert schema["maxLength"] == 100
        assert schema["minimum"] == 0
        assert schema["pattern"] == r"^[a-z]+$"

    def test_schema_builder_apply_metadata_constraints_empty_metadata(self):
        """Test applying constraints with empty metadata"""
        builder = SchemaBuilder({}, threading.Lock())
        schema = {}

        param_obj = Mock()
        param_obj.metadata = None

        builder._apply_metadata_constraints(schema, param_obj)
        assert schema == {}

        param_obj.metadata = []
        builder._apply_metadata_constraints(schema, param_obj)
        assert schema == {}

    def test_schema_builder_apply_metadata_constraints_no_metadata_attr(self):
        """Test applying constraints when no metadata attribute exists"""
        builder = SchemaBuilder({}, threading.Lock())
        schema = {}

        param_obj = Mock(spec=[])  # No attributes

        builder._apply_metadata_constraints(schema, param_obj)
        assert schema == {}

    def test_schema_builder_apply_object_metadata_none_values(self):
        """Test applying object metadata with None values"""
        builder = SchemaBuilder({}, threading.Lock())
        schema = {}

        param_obj = Mock()
        param_obj.title = None
        param_obj.description = None
        param_obj.example = None
        param_obj.examples = None
        param_obj.unknown = None

        builder._apply_object_metadata(schema, param_obj)
        assert schema == {}

    def test_schema_builder_apply_object_metadata_with_example(self):
        """Test applying object metadata with example value"""
        builder = SchemaBuilder({}, threading.Lock())
        schema = {}

        param_obj = Mock()
        param_obj.title = None
        param_obj.description = None
        param_obj.example = "laptop"
        param_obj.examples = None

        builder._apply_object_metadata(schema, param_obj)
        assert schema == {"example": "laptop"}

    def test_schema_builder_apply_default_value_none_or_ellipsis(self):
        """Test applying None or ellipsis default values"""
        builder = SchemaBuilder({}, threading.Lock())

        param_obj = Mock()
        param_obj.default = None
        schema = {}
        builder._apply_default_value(schema, param_obj)
        assert "default" not in schema

        param_obj.default = ...
        schema = {}
        builder._apply_default_value(schema, param_obj)
        assert "default" not in schema

    def test_schema_builder_apply_default_value_undefined_type(self):
        """Test applying PydanticUndefinedType default"""
        builder = SchemaBuilder({}, threading.Lock())
        schema = {}

        param_obj = Mock()
        param_obj.default = Mock()
        param_obj.default.__class__.__name__ = "PydanticUndefinedType"

        builder._apply_default_value(schema, param_obj)
        assert "default" not in schema

    def test_schema_builder_get_model_schema_new_model(self):
        """Test getting schema for new model"""
        definitions = {}
        builder = SchemaBuilder(definitions, threading.Lock())

        # Mock the schema that would be returned
        mock_schema = {"type": "object", "properties": {"name": {"type": "string"}}}

        def mock_cache_model_schema(model, cache_key):
            builder._model_schema_cache[cache_key] = mock_schema

        with patch.object(
            builder, "_cache_model_schema", side_effect=mock_cache_model_schema
        ):
            schema = builder.get_model_schema(SimpleModel)

            assert schema == {"$ref": "#/components/schemas/SimpleModel"}
            assert "SimpleModel" in definitions

    def test_schema_builder_get_model_schema_cached(self):
        """Test getting schema for cached model"""
        definitions = {}
        builder = SchemaBuilder(definitions, threading.Lock())

        # Pre-populate cache
        cache_key = f"{SimpleModel.__module__}.{SimpleModel.__name__}"
        builder._model_schema_cache[cache_key] = {"type": "object", "properties": {}}

        schema = builder.get_model_schema(SimpleModel)

        assert schema == {"$ref": "#/components/schemas/SimpleModel"}
        assert "SimpleModel" in definitions

    def test_schema_builder_cache_model_schema_with_definitions(self):
        """Test caching model schema with nested definitions"""
        builder = SchemaBuilder({}, threading.Lock())

        mock_schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "definitions": {"NestedType": {"type": "object"}},
            "$defs": {"AnotherType": {"type": "string"}},
        }

        with patch.object(SimpleModel, "model_json_schema", return_value=mock_schema):
            builder._cache_model_schema(SimpleModel, "test.SimpleModel")

        assert "NestedType" in builder.definitions
        assert "AnotherType" in builder.definitions
        assert "definitions" not in builder._model_schema_cache["test.SimpleModel"]
        assert "$defs" not in builder._model_schema_cache["test.SimpleModel"]

    def test_parameter_processor_init(self):
        """Test ParameterProcessor initialization"""
        schema_builder = Mock()
        processor = ParameterProcessor(schema_builder)

        assert processor.schema_builder is schema_builder

    def test_parameter_processor_process_route_parameters(self):
        """Test processing route parameters"""
        processor = ParameterProcessor(self.generator.schema_builder)

        def test_endpoint(name: str = Query(), age: int = Query(default=25)):
            pass

        route = Mock()
        route.endpoint = test_endpoint
        route.path = "/test"
        route.method = "GET"

        parameters, request_body = processor.process_route_parameters(route)

        assert len(parameters) >= 1
        assert request_body is None

    def test_parameter_processor_extract_path_parameters(self):
        """Test extracting path parameters from route path"""
        processor = ParameterProcessor(self.generator.schema_builder)

        path_params = processor._extract_path_parameters(
            "/users/<user_id>/posts/<int:post_id>"
        )

        assert "user_id" in path_params
        assert "post_id" in path_params

    def test_parameter_processor_should_skip_parameter_depends(self):
        """Test skipping Depends parameters"""
        processor = ParameterProcessor(self.generator.schema_builder)

        param = Mock()
        param.default = Depends(lambda: "test")

        assert processor._should_skip_parameter(param) is True

    def test_parameter_processor_should_skip_parameter_security(self):
        """Test skipping Security parameters"""
        processor = ParameterProcessor(self.generator.schema_builder)

        param = Mock()
        param.default = Security(lambda: "test")

        assert processor._should_skip_parameter(param) is True

    def test_parameter_processor_should_skip_parameter_normal(self):
        """Test not skipping normal parameters"""
        processor = ParameterProcessor(self.generator.schema_builder)

        param = Mock()
        param.default = Query()

        assert processor._should_skip_parameter(param) is False

    def test_parameter_processor_process_single_parameter_pydantic_model_get(self):
        """Test processing Pydantic model parameter for GET"""
        processor = ParameterProcessor(self.generator.schema_builder)

        param = Mock()
        param.annotation = SimpleModel

        result = processor._process_single_parameter("model", param, set(), "GET")

        assert result[0] == "parameters"
        assert isinstance(result[1], list)

    def test_parameter_processor_process_single_parameter_pydantic_model_post(self):
        """Test processing Pydantic model parameter for POST"""
        processor = ParameterProcessor(self.generator.schema_builder)

        param = Mock()
        param.annotation = SimpleModel
        param.default = inspect.Parameter.empty

        result = processor._process_single_parameter("model", param, set(), "POST")

        assert result[0] == "request_body"

    def test_parameter_processor_process_single_parameter_file(self):
        """Test processing File parameter"""
        processor = ParameterProcessor(self.generator.schema_builder)

        param = Mock()
        param.default = File()
        param.annotation = inspect.Parameter.empty

        result = processor._process_single_parameter("file", param, set(), "POST")

        assert result[0] == "multipart"

    def test_parameter_processor_process_single_parameter_file_annotation(self):
        """Test processing parameter with File annotation"""
        processor = ParameterProcessor(self.generator.schema_builder)

        param = Mock()
        param.default = inspect.Parameter.empty
        param.annotation = File

        result = processor._process_single_parameter("file", param, set(), "POST")

        assert result[0] == "multipart"

    def test_parameter_processor_process_single_parameter_form(self):
        """Test processing Form parameter"""
        processor = ParameterProcessor(self.generator.schema_builder)

        param = Mock()
        param.default = Form()

        result = processor._process_single_parameter("form_field", param, set(), "POST")

        assert result[0] == "form"

    def test_parameter_processor_process_single_parameter_body(self):
        """Test processing Body parameter"""
        processor = ParameterProcessor(self.generator.schema_builder)

        param = Mock()
        param.default = Body()

        result = processor._process_single_parameter("body", param, set(), "POST")

        assert result[0] == "request_body"

    def test_parameter_processor_process_single_parameter_regular(self):
        """Test processing regular parameter"""
        processor = ParameterProcessor(self.generator.schema_builder)

        param = Mock()
        param.default = Query()

        with patch.object(
            processor, "_build_parameter_info", return_value={"name": "test"}
        ):
            result = processor._process_single_parameter("param", param, set(), "GET")

        assert result[0] == "parameter"

    def test_parameter_processor_process_single_parameter_none_result(self):
        """Test processing parameter that returns None"""
        processor = ParameterProcessor(self.generator.schema_builder)

        param = Mock()
        param.default = Query()

        with patch.object(processor, "_build_parameter_info", return_value=None):
            result = processor._process_single_parameter("param", param, set(), "GET")

        assert result is None

    def test_parameter_processor_build_parameter_info_exclude_from_schema(self):
        """Test building parameter info when excluded from schema"""
        processor = ParameterProcessor(self.generator.schema_builder)

        param = Mock()
        param.default = Query(include_in_schema=False)

        result = processor._build_parameter_info("param", param, set())

        assert result is None

    def test_parameter_processor_build_parameter_info_form_param(self):
        """Test building parameter info for Form parameter (should return None)"""
        processor = ParameterProcessor(self.generator.schema_builder)

        param = Mock()
        param.default = Form()

        result = processor._build_parameter_info("param", param, set())

        assert result is None

    def test_parameter_processor_build_parameter_info_body_param(self):
        """Test building parameter info for Body parameter (should return None)"""
        processor = ParameterProcessor(self.generator.schema_builder)

        param = Mock()
        param.default = Body()

        result = processor._build_parameter_info("param", param, set())

        assert result is None

    def test_parameter_processor_determine_parameter_location_query(self):
        """Test determining parameter location as query"""
        processor = ParameterProcessor(self.generator.schema_builder)

        location, name = processor._determine_parameter_location_and_name(
            "param", Query(), set()
        )

        assert location == "query"
        assert name == "param"

    def test_parameter_processor_determine_parameter_location_header_with_alias(self):
        """Test determining header parameter location with alias"""
        processor = ParameterProcessor(self.generator.schema_builder)

        location, name = processor._determine_parameter_location_and_name(
            "param", Header(alias="X-Custom"), set()
        )

        assert location == "header"
        assert name == "X-Custom"

    def test_param_processor_determine_parameter_location_header_convert_underscores(
        self,
    ):
        """Test determining header parameter location with underscore conversion"""
        processor = ParameterProcessor(self.generator.schema_builder)

        location, name = processor._determine_parameter_location_and_name(
            "user_agent", Header(), set()
        )

        assert location == "header"
        assert name == "user-agent"

    def test_parameter_processor_determine_parameter_location_header_no_conversion(
        self,
    ):
        """Test determining header parameter location without underscore conversion"""
        processor = ParameterProcessor(self.generator.schema_builder)

        location, name = processor._determine_parameter_location_and_name(
            "user_agent", Header(convert_underscores=False), set()
        )

        assert location == "header"
        assert name == "user_agent"

    def test_parameter_processor_determine_parameter_location_path_param(self):
        """Test determining parameter location for path parameter"""
        processor = ParameterProcessor(self.generator.schema_builder)

        location, name = processor._determine_parameter_location_and_name(
            "user_id", "default", {"user_id"}
        )

        assert location == "path"
        assert name == "user_id"

    def test_parameter_processor_is_parameter_required_param_ellipsis(self):
        """Test parameter required check for Param with default value"""
        processor = ParameterProcessor(self.generator.schema_builder)

        # Test with query parameter that has explicit default value
        param_obj = Query(default="default_value")
        param = Mock()

        result = processor._is_parameter_required(param_obj, param, "query")
        assert result is False  # Has default, so not required

        # Test path parameter (always required regardless of default)
        result = processor._is_parameter_required(param_obj, param, "path")
        assert result is True  # Path params are always required

    def test_parameter_processor_is_parameter_required_path_param(self):
        """Test parameter required check for path parameter"""
        processor = ParameterProcessor(self.generator.schema_builder)

        param_obj = Query(default="test")
        param = Mock()

        result = processor._is_parameter_required(param_obj, param, "path")

        assert result is True

    def test_parameter_processor_is_parameter_required_empty_param(self):
        """Test parameter required check for empty parameter"""
        processor = ParameterProcessor(self.generator.schema_builder)

        param_obj = "not_param"
        param = Mock()
        param.default = inspect.Parameter.empty

        result = processor._is_parameter_required(param_obj, param, "query")

        assert result is True

    def test_parameter_processor_add_parameter_metadata_with_param_obj(self):
        """Test adding parameter metadata from Param object"""
        processor = ParameterProcessor(self.generator.schema_builder)

        param_info = {}
        param_obj = Query(
            description="Test description", examples=["example1"], deprecated=True
        )

        processor._add_parameter_metadata(param_info, param_obj, "param")

        assert param_info["description"] == "Test description"
        assert "examples" in param_info
        assert param_info["deprecated"] is True

    def test_parameter_processor_add_parameter_metadata_with_example(self):
        """Test adding parameter metadata with example (singular)"""
        processor = ParameterProcessor(self.generator.schema_builder)

        param_info = {}
        param_obj = Query(example="laptop")

        processor._add_parameter_metadata(param_info, param_obj, "search")

        assert param_info["example"] == "laptop"

    def test_parameter_processor_add_parameter_metadata_common_descriptions(self):
        """Test adding common parameter descriptions"""
        processor = ParameterProcessor(self.generator.schema_builder)

        param_info = {}
        param_obj = Query()

        processor._add_parameter_metadata(param_info, param_obj, "page")

        assert param_info["description"] == "Pagination page"

    def test_parameter_processor_build_form_field_schema(self):
        """Test building form field schema"""
        processor = ParameterProcessor(self.generator.schema_builder)

        param = Mock()
        param.annotation = str
        param.default = Form()

        schema = processor._build_form_field_schema("field", param)

        assert "type" in schema

    def test_parameter_processor_build_file_field_schema(self):
        """Test building file field schema"""
        processor = ParameterProcessor(self.generator.schema_builder)

        param = Mock()
        param.default = File(description="Upload file")

        schema = processor._build_file_field_schema("file", param)

        assert schema["type"] == "string"
        assert schema["format"] == "binary"
        assert schema["description"] == "Upload file"

    def test_parameter_processor_build_file_field_schema_no_description(self):
        """Test building file field schema without description"""
        processor = ParameterProcessor(self.generator.schema_builder)

        param = Mock()
        param.default = File()
        param.default.description = None

        schema = processor._build_file_field_schema("file", param)

        assert schema["type"] == "string"
        assert schema["format"] == "binary"
        assert "description" not in schema

    def test_parameter_processor_build_body_request_body(self):
        """Test building request body for Body parameter"""
        processor = ParameterProcessor(self.generator.schema_builder)

        param = Mock()
        param.default = Body(media_type="application/xml", description="XML body")
        param.default.default = ...

        with patch.object(
            processor.schema_builder,
            "build_parameter_schema_from_param",
            return_value={"type": "string"},
        ):
            request_body = processor._build_body_request_body(param)

        assert "application/xml" in request_body["content"]
        assert request_body["required"] is True
        assert request_body["description"] == "XML body"

    def test_parameter_processor_build_form_request_body_multipart(self):
        """Test building multipart form request body"""
        processor = ParameterProcessor(self.generator.schema_builder)

        form_fields = {"name": {"type": "string"}}
        multipart_fields = {"file": {"type": "string", "format": "binary"}}

        request_body = processor._build_form_request_body(form_fields, multipart_fields)

        assert "multipart/form-data" in request_body["content"]
        assert (
            "name"
            in request_body["content"]["multipart/form-data"]["schema"]["properties"]
        )
        assert (
            "file"
            in request_body["content"]["multipart/form-data"]["schema"]["properties"]
        )

    def test_parameter_processor_build_form_request_body_urlencoded(self):
        """Test building URL-encoded form request body"""
        processor = ParameterProcessor(self.generator.schema_builder)

        form_fields = {"username": {"type": "string"}}
        multipart_fields = {}

        request_body = processor._build_form_request_body(form_fields, multipart_fields)

        assert "application/x-www-form-urlencoded" in request_body["content"]

    def test_parameter_processor_build_form_request_body_empty(self):
        """Test building request body with no fields"""
        processor = ParameterProcessor(self.generator.schema_builder)

        request_body = processor._build_form_request_body({}, {})

        assert request_body is None

    def test_parameter_processor_build_query_params_from_model(self):
        """Test building query parameters from model"""
        processor = ParameterProcessor(self.generator.schema_builder)

        parameters = processor._build_query_params_from_model(SimpleModel)

        assert len(parameters) > 0
        param_names = [p["name"] for p in parameters]
        assert "name" in param_names
        assert "age" in param_names

    def test_parameter_processor_is_pydantic_model_true(self):
        """Test Pydantic model detection - positive"""
        processor = ParameterProcessor(self.generator.schema_builder)

        assert processor._is_pydantic_model(SimpleModel) is True

    def test_parameter_processor_is_pydantic_model_false(self):
        """Test Pydantic model detection - negative"""
        processor = ParameterProcessor(self.generator.schema_builder)

        assert processor._is_pydantic_model(str) is False
        assert processor._is_pydantic_model("not_a_class") is False

    def test_response_builder_init(self):
        """Test ResponseBuilder initialization"""
        schema_builder = Mock()
        builder = ResponseBuilder(schema_builder)

        assert builder.schema_builder is schema_builder

    def test_response_builder_build_responses_basic(self):
        """Test building basic responses"""
        builder = ResponseBuilder(self.generator.schema_builder)

        route = Mock()
        route.meta = {}

        responses = builder.build_responses(route)

        assert "200" in responses
        assert responses["200"]["description"] == "OK"

    def test_response_builder_build_responses_custom_status(self):
        """Test building responses with custom status code"""
        builder = ResponseBuilder(self.generator.schema_builder)

        route = Mock()
        route.meta = {"status_code": 201}

        responses = builder.build_responses(route)

        assert "201" in responses
        assert responses["201"]["description"] == "Created"

    def test_response_builder_add_response_model_pydantic(self):
        """Test adding Pydantic response model"""
        builder = ResponseBuilder(self.generator.schema_builder)

        responses = {"200": {"description": "OK"}}

        builder._add_response_model(responses, "200", SimpleModel)

        assert "content" in responses["200"]
        assert "application/json" in responses["200"]["content"]

    def test_response_builder_add_response_model_list_pydantic(self):
        """Test adding list of Pydantic models as response"""
        builder = ResponseBuilder(self.generator.schema_builder)

        responses = {"200": {"description": "OK"}}

        builder._add_response_model(responses, "200", list[SimpleModel])

        assert "content" in responses["200"]
        schema = responses["200"]["content"]["application/json"]["schema"]
        assert schema["type"] == "array"
        assert "$ref" in schema["items"]

    def test_response_builder_add_response_model_list_non_pydantic(self):
        """Test adding list of non-Pydantic types"""
        builder = ResponseBuilder(self.generator.schema_builder)

        responses = {"200": {"description": "OK"}}

        builder._add_response_model(responses, "200", list[str])

        # Should not add content for non-Pydantic types
        assert "content" not in responses["200"]

    def test_response_builder_add_response_model_non_pydantic(self):
        """Test adding non-Pydantic response model"""
        builder = ResponseBuilder(self.generator.schema_builder)

        responses = {"200": {"description": "OK"}}

        builder._add_response_model(responses, "200", str)

        # Should not add content for non-Pydantic types
        assert "content" not in responses["200"]

    def test_response_builder_add_custom_error_responses(self):
        """Test adding custom error responses"""
        builder = ResponseBuilder(self.generator.schema_builder)

        route = Mock()
        route.meta = {"response_errors": [400, 404, 500]}

        responses = {}
        builder._add_custom_error_responses(responses, route)

        assert "400" in responses
        assert "404" in responses
        assert "500" in responses

    def test_response_builder_add_custom_error_responses_none(self):
        """Test not adding custom errors when none specified"""
        builder = ResponseBuilder(self.generator.schema_builder)

        route = Mock()
        route.meta = {}

        responses = {}
        builder._add_custom_error_responses(responses, route)

        assert len(responses) == 0

    def test_openapi_generator_init(self):
        """Test OpenAPIGenerator initialization"""
        generator = OpenAPIGenerator(self.router)

        assert generator.router is self.router
        assert generator.definitions == {}
        assert isinstance(generator._cache_lock, type(threading.Lock()))

    def test_openapi_generator_generate(self):
        """Test generating complete OpenAPI schema"""
        schema = self.generator.generate()

        assert schema["openapi"] == "3.0.0"
        assert schema["info"]["title"] == "Test API"
        assert schema["info"]["version"] == "1.0.0"
        assert "paths" in schema
        assert "components" in schema

    def test_openapi_generator_build_paths(self):
        """Test building paths section"""

        @self.router.get("/test")
        def test_endpoint():
            pass

        paths = self.generator._build_paths()

        assert "/test" in paths
        assert "get" in paths["/test"]

    def test_openapi_generator_build_base_schema(self):
        """Test building base schema structure"""
        paths = {"/test": {"get": {"summary": "Test"}}}

        schema = self.generator._build_base_schema(paths)

        assert schema["openapi"] == self.router.openapi_version
        assert schema["info"]["title"] == self.router.title
        assert schema["paths"] is paths

    def test_openapi_generator_add_security_schemes(self):
        """Test adding security schemes"""
        schema = {"components": {}}

        self.generator._add_security_schemes(schema)

        assert "securitySchemes" in schema["components"]

    def test_openapi_generator_add_security_schemes_none(self):
        """Test not adding security schemes when none"""
        router = BaseRouter(security_scheme=None)  # Explicitly set no security scheme
        generator = OpenAPIGenerator(router)
        schema = {"components": {}}

        generator._add_security_schemes(schema)

        assert "securitySchemes" not in schema["components"]

    def test_openapi_generator_add_global_security(self):
        """Test adding global security"""
        self.router._global_security = [{"BearerAuth": []}]
        schema = {}

        self.generator._add_global_security(schema)

        assert "security" in schema

    def test_openapi_generator_add_global_security_empty(self):
        """Test not adding global security when empty"""
        self.router._global_security = []
        schema = {}

        self.generator._add_global_security(schema)

        assert "security" not in schema

    def test_openapi_generator_has_security_dependency_true(self):
        """Test detecting security dependency"""

        def endpoint(user: dict = Security(lambda: {}, scopes=["read"])):
            pass

        route = Mock()
        route.endpoint = endpoint

        result = self.generator._has_security_dependency(route)

        assert result is True

    def test_openapi_generator_has_security_dependency_false(self):
        """Test not detecting security dependency"""

        def endpoint(param: str):
            pass

        route = Mock()
        route.endpoint = endpoint

        result = self.generator._has_security_dependency(route)

        assert result is False

    def test_openapi_generator_extract_security_scopes(self):
        """Test extracting security scopes"""

        def endpoint(
            user: dict = Security(lambda: {}, scopes=["read", "write"]),
            admin: dict = Security(lambda: {}, scopes=["admin"]),
        ):
            pass

        route = Mock()
        route.endpoint = endpoint

        scopes = self.generator._extract_security_scopes(route)

        assert "read" in scopes
        assert "write" in scopes
        assert "admin" in scopes

    def test_openapi_generator_extract_security_scopes_none(self):
        """Test extracting scopes when none exist"""

        def endpoint(param: str):
            pass

        route = Mock()
        route.endpoint = endpoint

        scopes = self.generator._extract_security_scopes(route)

        assert scopes == []

    def test_openapi_generator_build_operation_with_security_auto_add(self):
        """Test auto-adding security to operation"""

        def endpoint(user: dict = Security(lambda: {}, scopes=["read"])):
            pass

        route = Mock()
        route.endpoint = endpoint
        route.method = "GET"
        route.meta = {}
        route.path = "/protected"  # Provide actual string path

        operation = self.generator._build_operation(route)

        assert "security" in operation
        assert operation["security"][0]["BearerAuth"] == ["read"]

    def test_openapi_generator_build_operation_no_auto_security(self):
        """Test not auto-adding security when no schemes"""
        router = BaseRouter(security_scheme=None)  # No security scheme
        generator = OpenAPIGenerator(router)

        def endpoint(user: dict = Security(lambda: {}, scopes=["read"])):
            pass

        route = Mock()
        route.endpoint = endpoint
        route.method = "GET"
        route.meta = {}
        route.path = "/test"  # Provide actual string path

        operation = generator._build_operation(route)

        assert "security" not in operation

    def test_openapi_generator_add_optional_operation_fields(self):
        """Test adding optional operation fields"""
        operation = {}

        route = Mock()
        route.meta = {
            "tags": ["test"],
            "deprecated": True,
            "security": [{"ApiKey": []}],
            "description": "Custom description",
        }

        parameters = [{"name": "param", "in": "query"}]
        request_body = {"content": {"application/json": {}}}

        self.generator._add_optional_operation_fields(
            operation, route, parameters, request_body
        )

        assert operation["parameters"] == parameters
        assert operation["requestBody"] == request_body
        assert operation["tags"] == ["test"]
        assert operation["deprecated"] is True
        assert operation["security"] == [{"ApiKey": []}]
        assert operation["description"] == "Custom description"

    def test_openapi_generator_add_optional_operation_fields_empty(self):
        """Test not adding optional fields when empty"""
        operation = {}

        route = Mock()
        route.meta = {}

        self.generator._add_optional_operation_fields(operation, route, [], None)

        assert "parameters" not in operation
        assert "requestBody" not in operation
        assert "tags" not in operation

    def test_parameter_info_dataclass(self):
        """Test ParameterInfo dataclass"""
        param_info = ParameterInfo(
            name="test",
            location="query",
            schema={"type": "string"},
            required=True,
            description="Test parameter",
            examples={"example1": {"value": "test"}},
            deprecated=True,
        )

        assert param_info.name == "test"
        assert param_info.location == "query"
        assert param_info.required is True
        assert param_info.deprecated is True

    def test_parameter_processor_build_parameter_schema_no_type(self):
        """Test building parameter schema when no type in schema"""
        processor = ParameterProcessor(self.generator.schema_builder)

        param = Mock()
        param.annotation = str
        param.default = Form()

        with patch.object(
            processor.schema_builder,
            "build_parameter_schema_from_param",
            return_value={},
        ):
            schema = processor._build_form_field_schema("field", param)

        assert schema["type"] == "string"

    def test_summary_from_decorator_meta(self):
        """Summary from decorator should override docstring"""

        @self.router.get("/with-summary", summary="Custom summary")
        def endpoint_with_summary():
            """Docstring summary"""

        schema = self.generator.generate()
        operation = schema["paths"]["/with-summary"]["get"]
        assert operation["summary"] == "Custom summary"

    def test_summary_falls_back_to_function_name(self):
        """Summary should fallback to function name titlecase (FastAPI-like)"""

        @self.router.get("/with-docstring")
        def get_user_profile():
            """This is a docstring"""

        schema = self.generator.generate()
        operation = schema["paths"]["/with-docstring"]["get"]
        assert operation["summary"] == "Get User Profile"

    def test_summary_function_name_when_no_docstring(self):
        """Summary should be function name titlecase when no meta and no docstring"""

        @self.router.get("/no-summary")
        def create_new_item():
            pass

        schema = self.generator.generate()
        operation = schema["paths"]["/no-summary"]["get"]
        assert operation["summary"] == "Create New Item"

    def test_description_from_docstring(self):
        """Docstring should become description (FastAPI-like)"""

        @self.router.get("/with-desc")
        def some_endpoint():
            """This endpoint does something"""

        schema = self.generator.generate()
        operation = schema["paths"]["/with-desc"]["get"]
        assert operation["description"] == "This endpoint does something"

    def test_description_from_meta_overrides_docstring(self):
        """Explicit description in decorator overrides docstring"""

        @self.router.get("/with-meta-desc", description="Explicit description")
        def some_endpoint():
            """Docstring description"""

        schema = self.generator.generate()
        operation = schema["paths"]["/with-meta-desc"]["get"]
        assert operation["description"] == "Explicit description"

    def test_no_description_when_no_docstring(self):
        """No description field when no docstring and no meta description"""

        @self.router.get("/no-desc")
        def some_endpoint():
            pass

        schema = self.generator.generate()
        operation = schema["paths"]["/no-desc"]["get"]
        assert "description" not in operation

    def test_operation_id_from_decorator_meta(self):
        """operation_id from decorator should override auto-generated"""

        @self.router.get("/custom-op", operation_id="my_custom_op")
        def some_endpoint():
            pass

        schema = self.generator.generate()
        operation = schema["paths"]["/custom-op"]["get"]
        assert operation["operationId"] == "my_custom_op"

    def test_operation_id_falls_back_to_auto(self):
        """operation_id should auto-generate when not in meta"""

        @self.router.get("/auto-op")
        def auto_op_endpoint():
            pass

        schema = self.generator.generate()
        operation = schema["paths"]["/auto-op"]["get"]
        assert operation["operationId"] == "get_auto_op_endpoint"

    def test_responses_dict_from_decorator(self):
        """Responses dict from decorator should add to OpenAPI responses"""

        @self.router.get(
            "/with-responses",
            responses={
                404: {"description": "Item not found"},
                409: {"description": "Conflict"},
            },
        )
        def endpoint_with_responses():
            pass

        schema = self.generator.generate()
        responses = schema["paths"]["/with-responses"]["get"]["responses"]
        assert "404" in responses
        assert responses["404"]["description"] == "Item not found"
        assert "409" in responses
        assert responses["409"]["description"] == "Conflict"

    def test_responses_dict_merges_with_existing(self):
        """Responses dict should merge description into existing response"""

        @self.router.get(
            "/merge-responses",
            status_code=200,
            response_model=SimpleModel,
            responses={200: {"description": "Custom success description"}},
        )
        def endpoint_merge():
            pass

        schema = self.generator.generate()
        responses = schema["paths"]["/merge-responses"]["get"]["responses"]
        assert responses["200"]["description"] == "Custom success description"
        # Should still have content schema
        assert "content" in responses["200"]

    def test_response_errors_still_works(self):
        """Existing response_errors parameter should still work"""

        @self.router.post("/with-errors", response_errors=[400, 500])
        def endpoint_with_errors(data: ComplexModel):
            pass

        schema = self.generator.generate()
        responses = schema["paths"]["/with-errors"]["post"]["responses"]
        assert "400" in responses
        assert "500" in responses

    def test_responses_and_response_errors_together(self):
        """Both responses and response_errors can coexist"""

        @self.router.post(
            "/both",
            response_errors=[400],
            responses={404: {"description": "Not found"}},
        )
        def endpoint_both(data: ComplexModel):
            pass

        schema = self.generator.generate()
        responses = schema["paths"]["/both"]["post"]["responses"]
        assert "400" in responses
        assert "404" in responses
        assert responses["404"]["description"] == "Not found"

    def test_responses_with_model(self):
        """Responses with model key should generate $ref schema (FastAPI-like)"""

        class ErrorDetail(BaseModel):
            detail: str
            code: int

        @self.router.get(
            "/with-model-response",
            responses={
                404: {"description": "Not found", "model": ErrorDetail},
                422: {"description": "Validation error", "model": ErrorDetail},
            },
        )
        def endpoint_with_model():
            pass

        schema = self.generator.generate()
        responses = schema["paths"]["/with-model-response"]["get"]["responses"]
        assert responses["404"]["description"] == "Not found"
        assert responses["404"]["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/ErrorDetail"
        }
        assert responses["422"]["description"] == "Validation error"
        assert responses["422"]["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/ErrorDetail"
        }
        assert "ErrorDetail" in schema["components"]["schemas"]

    def test_responses_model_merges_with_existing(self):
        """Responses with model should update schema on existing response codes"""

        class SuccessDetail(BaseModel):
            message: str

        @self.router.get(
            "/merge-model",
            status_code=200,
            response_model=SimpleModel,
            responses={200: {"description": "Custom OK", "model": SuccessDetail}},
        )
        def endpoint_merge_model():
            pass

        schema = self.generator.generate()
        responses = schema["paths"]["/merge-model"]["get"]["responses"]
        assert responses["200"]["description"] == "Custom OK"
        assert responses["200"]["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/SuccessDetail"
        }

    def test_responses_without_model_uses_error_schema(self):
        """Responses without model key should still use ErrorSchema"""

        @self.router.get(
            "/no-model",
            responses={404: {"description": "Not found"}},
        )
        def endpoint_no_model():
            pass

        schema = self.generator.generate()
        responses = schema["paths"]["/no-model"]["get"]["responses"]
        assert responses["404"]["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/ErrorSchema"
        }

    def test_responses_non_dict_value(self):
        """Non-dict response_info should use default description and ErrorSchema"""

        @self.router.get(
            "/non-dict",
            responses={404: "some string", 500: 0},
        )
        def endpoint_non_dict():
            pass

        schema = self.generator.generate()
        responses = schema["paths"]["/non-dict"]["get"]["responses"]
        assert responses["404"]["description"] == "Not Found"
        assert responses["404"]["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/ErrorSchema"
        }
        assert responses["500"]["description"] == "Internal Server Error"
