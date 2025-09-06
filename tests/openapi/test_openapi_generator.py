from pydantic import BaseModel, computed_field

from fastopenapi.core.params import Cookie, Header
from fastopenapi.core.router import BaseRouter
from fastopenapi.openapi.generator import OpenAPIGenerator


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


class TestOpenAPIGenerator:
    def setup_method(self):
        self.router = BaseRouter(
            title="Test API",
            version="1.0.0",
            description="Test API Description",
        )
        self.generator = OpenAPIGenerator(self.router)

    def test_generate_basic(self):
        # Test generating a basic OpenAPI schema

        @self.router.get("/test")
        def test_endpoint():
            """Test endpoint"""

        schema = self.generator.generate()

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

    def test_generate_with_path_params(self):
        # Test OpenAPI generation with path parameters

        @self.router.get("/users/{user_id}")
        def get_user(user_id: int):
            pass

        schema = self.generator.generate()

        # Path should be converted to OpenAPI format
        assert "/users/{user_id}" in schema["paths"]

        # Check parameters
        parameters = schema["paths"]["/users/{user_id}"]["get"]["parameters"]
        assert len(parameters) == 1
        assert parameters[0]["name"] == "user_id"
        assert parameters[0]["in"] == "path"
        assert parameters[0]["required"] is True
        assert parameters[0]["schema"]["type"] == "integer"

    def test_generate_with_query_params(self):
        # Test OpenAPI generation with query parameters

        @self.router.get("/search")
        def search(q: str, limit: int = 10):
            pass

        schema = self.generator.generate()

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

    def test_generate_with_header_params(self):
        # Test OpenAPI generation with header parameters

        @self.router.get("/auth")
        def auth_endpoint(authorization: str = Header()):
            pass

        schema = self.generator.generate()

        # Check parameters
        parameters = schema["paths"]["/auth"]["get"]["parameters"]
        assert len(parameters) == 1
        assert parameters[0]["name"] == "authorization"
        assert parameters[0]["in"] == "header"
        assert parameters[0]["required"] is False

    def test_generate_with_cookie_params(self):
        # Test OpenAPI generation with cookie parameters

        @self.router.get("/session")
        def session_endpoint(session_id: str = Cookie()):
            pass

        schema = self.generator.generate()

        # Check parameters
        parameters = schema["paths"]["/session"]["get"]["parameters"]
        assert len(parameters) == 1
        assert parameters[0]["name"] == "session_id"
        assert parameters[0]["in"] == "cookie"
        assert parameters[0]["required"] is False

    def test_generate_with_request_body(self):
        # Test OpenAPI generation with request body (Pydantic model)

        @self.router.post("/users")
        def create_user(user: TestModel):
            pass

        schema = self.generator.generate()

        # Check request body
        request_body = schema["paths"]["/users"]["post"]["requestBody"]
        assert request_body["required"] is True
        assert "application/json" in request_body["content"]
        assert "$ref" in request_body["content"]["application/json"]["schema"]

        # Check that model schema is in components
        ref = request_body["content"]["application/json"]["schema"]["$ref"]
        assert ref == "#/components/schemas/TestModel"
        assert "TestModel" in schema["components"]["schemas"]

    def test_generate_with_response_model(self):
        # Test OpenAPI generation with response model

        @self.router.post("/users", response_model=ResponseModel)
        def create_user(user: TestModel):
            pass

        schema = self.generator.generate()

        # Check response
        response = schema["paths"]["/users"]["post"]["responses"]["200"]
        assert "content" in response
        assert "application/json" in response["content"]
        assert "$ref" in response["content"]["application/json"]["schema"]

        # Check that response model schema is in components
        ref = response["content"]["application/json"]["schema"]["$ref"]
        assert ref == "#/components/schemas/ResponseModel"
        assert "ResponseModel" in schema["components"]["schemas"]

    def test_generate_with_list_response(self):
        # Test OpenAPI generation with List response model

        @self.router.get("/users", response_model=list[ResponseModel])
        def list_users():
            pass

        schema = self.generator.generate()

        # Check response
        response = schema["paths"]["/users"]["get"]["responses"]["200"]
        assert "content" in response
        assert "application/json" in response["content"]

        # Check array schema
        array_schema = response["content"]["application/json"]["schema"]
        assert array_schema["type"] == "array"
        assert "$ref" in array_schema["items"]
        assert array_schema["items"]["$ref"] == "#/components/schemas/ResponseModel"

    def test_generate_with_status_code(self):
        # Test OpenAPI generation with custom status code

        @self.router.post("/users", status_code=201)
        def create_user():
            pass

        schema = self.generator.generate()

        # Check response has correct status code
        assert "201" in schema["paths"]["/users"]["post"]["responses"]
        assert "description" in schema["paths"]["/users"]["post"]["responses"]["201"]
        assert (
            schema["paths"]["/users"]["post"]["responses"]["201"]["description"]
            == "Created"
        )

    def test_generate_with_response_errors(self):
        # Test OpenAPI generation with response errors

        @self.router.post("/users", response_errors=[400, 404, 500])
        def create_user(user: TestModel):
            pass

        schema = self.generator.generate()

        responses = schema["paths"]["/users"]["post"]["responses"]
        assert "200" in responses
        assert "400" in responses
        assert "404" in responses
        assert "500" in responses

        # Check error schema reference
        assert "ErrorSchema" in schema["components"]["schemas"]

    def test_generate_with_deprecated(self):
        # Test OpenAPI generation with deprecated flag

        @self.router.get("/old", deprecated=True)
        def old_endpoint():
            pass

        schema = self.generator.generate()

        # Check deprecated flag
        assert schema["paths"]["/old"]["get"]["deprecated"] is True

    def test_generate_with_tags(self):
        # Test OpenAPI generation with tags

        @self.router.get("/users", tags=["users", "admin"])
        def get_users():
            pass

        schema = self.generator.generate()

        # Check tags
        assert schema["paths"]["/users"]["get"]["tags"] == ["users", "admin"]

    def test_build_query_params_from_model(self):
        # Test building query parameters from Pydantic model for GET

        @self.router.get("/search")
        def search(query: TestModel):
            pass

        schema = self.generator.generate()

        # Should convert model to query parameters
        params = schema["paths"]["/search"]["get"]["parameters"]
        assert len(params) == 4

        names = [p["name"] for p in params]
        assert "name" in names
        assert "age" in names
        assert "is_active" in names
        assert "$active" in names  # alias
