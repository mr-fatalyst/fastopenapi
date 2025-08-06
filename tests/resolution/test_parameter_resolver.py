import pytest
from pydantic import BaseModel, computed_field

from fastopenapi.core.types import Cookie, Form, Header, UploadFile
from fastopenapi.errors.exceptions import BadRequestError, ValidationError
from fastopenapi.resolution.resolver import ParameterResolver


class TestModel(BaseModel):
    name: str
    age: int
    is_active: bool = True

    @computed_field(alias="$active")
    def aliased_is_active(self) -> bool:
        return self.is_active


class TestParameterResolver:
    def setup_method(self):
        self.resolver = ParameterResolver()

    def test_resolve_with_primitive_types(self):
        # Test resolving endpoint parameters with primitive types
        from fastopenapi.core.types import RequestData

        def endpoint(name: str, age: int, active: bool = False):
            return {"name": name, "age": age, "active": active}

        request_data = RequestData(query_params={"name": "John", "age": "30"})

        result = self.resolver.resolve(endpoint, request_data)

        assert result["name"] == "John"
        assert result["age"] == 30
        assert result["active"] is False

    def test_resolve_with_pydantic_model(self):
        # Test resolving endpoint parameters with Pydantic model
        from fastopenapi.core.types import RequestData

        def endpoint(user: TestModel):
            return user

        request_data = RequestData(body={"name": "John", "age": 30})

        result = self.resolver.resolve(endpoint, request_data)

        assert isinstance(result["user"], TestModel)
        assert result["user"].name == "John"
        assert result["user"].age == 30
        assert result["user"].is_active is True  # Default value

    def test_resolve_missing_required(self):
        # Test error when required parameter is missing
        from fastopenapi.core.types import RequestData

        def endpoint(name: str, age: int):
            pass

        request_data = RequestData(query_params={"name": "John"})

        with pytest.raises(BadRequestError) as excinfo:
            self.resolver.resolve(endpoint, request_data)

        assert "Missing required parameter" in str(excinfo.value)
        assert "age" in str(excinfo.value)

    def test_resolve_invalid_type(self):
        # Test error when parameter type is invalid
        from fastopenapi.core.types import RequestData

        def endpoint(age: int):
            pass

        request_data = RequestData(query_params={"age": "not_an_integer"})

        with pytest.raises(BadRequestError) as excinfo:
            self.resolver.resolve(endpoint, request_data)

        assert "Error parsing parameter" in str(excinfo.value)

    def test_resolve_model_validation_error(self):
        # Test error when model validation fails
        from fastopenapi.core.types import RequestData

        def endpoint(user: TestModel):
            pass

        request_data = RequestData(
            body={"name": "John"}  # Missing required 'age' field
        )

        with pytest.raises(ValidationError) as excinfo:
            self.resolver.resolve(endpoint, request_data)

        assert "Validation error for parameter" in str(excinfo.value)

    def test_resolve_with_header_param(self):
        # Test resolving header parameters
        from fastopenapi.core.types import RequestData

        def endpoint(x_api_key: str = Header()):
            return x_api_key

        request_data = RequestData(headers={"x-api-key": "secret123"})

        result = self.resolver.resolve(endpoint, request_data)
        assert result["x_api_key"] == "secret123"

    def test_resolve_with_cookie_param(self):
        # Test resolving cookie parameters
        from fastopenapi.core.types import RequestData

        def endpoint(session_id: str = Cookie()):
            return session_id

        request_data = RequestData(cookies={"session_id": "abc123"})

        result = self.resolver.resolve(endpoint, request_data)
        assert result["session_id"] == "abc123"

    def test_resolve_with_form_param(self):
        # Test resolving form parameters
        from fastopenapi.core.types import RequestData

        def endpoint(username: str = Form()):
            return username

        request_data = RequestData(form_data={"username": "john_doe"})

        result = self.resolver.resolve(endpoint, request_data)
        assert result["username"] == "john_doe"

    def test_resolve_with_file_upload(self):
        # Test resolving file upload
        from fastopenapi.core.types import RequestData

        def endpoint(file: UploadFile):
            return file

        mock_file = UploadFile(
            filename="test.txt", content_type="text/plain", file=b"content"
        )

        request_data = RequestData(files={"file": mock_file})

        result = self.resolver.resolve(endpoint, request_data)
        assert result["file"] == mock_file

    def test_resolve_with_path_params(self):
        # Test resolving path parameters
        from fastopenapi.core.types import RequestData

        def endpoint(user_id: int, name: str):
            return {"user_id": user_id, "name": name}

        request_data = RequestData(
            path_params={"user_id": "123"}, query_params={"name": "John"}
        )

        result = self.resolver.resolve(endpoint, request_data)
        assert result["user_id"] == 123
        assert result["name"] == "John"
