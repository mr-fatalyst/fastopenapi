from typing import Any, Optional
from unittest.mock import Mock

from pydantic import BaseModel, Field

from fastopenapi.core.constants import SecuritySchemeType
from fastopenapi.core.params import Body, Depends, File, Form, Header, Query, Security
from fastopenapi.core.router import BaseRouter
from fastopenapi.openapi.generator import (
    OpenAPIGenerator,
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


class TestOpenAPIGeneratorAdvanced:
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

    # TODO determine why not nullable
    # def test_union_types(self):
    #     """Test Union type handling"""
    #
    #     @self.router.get("/union")
    #     def union_endpoint(
    #         value: str | int = Query(), optional: str | None = Query(default=None)
    #     ):
    #         pass
    #
    #     schema = self.generator.generate()
    #     params = schema["paths"]["/union"]["get"]["parameters"]
    #
    #     value_param = next(p for p in params if p["name"] == "value")
    #     optional_param = next(p for p in params if p["name"] == "optional")
    #
    #     # Union should default to string
    #     assert value_param["schema"]["type"] == "string"
    #     assert optional_param["schema"]["nullable"] is True

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

    def test_parameter_processor_file_upload(self):
        """Test ParameterProcessor file upload handling"""

        def test_func(file: bytes = File(description="Upload file")):
            pass

        route = Mock()
        route.endpoint = test_func
        route.method = "POST"
        route.path = "/upload"

        processor = ParameterProcessor(self.generator.schema_builder)
        parameters, request_body = processor.process_route_parameters(route)

        assert request_body is not None
        assert "multipart/form-data" in request_body["content"]

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
