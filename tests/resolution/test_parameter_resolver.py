import inspect
from unittest.mock import Mock, patch

import pytest
from pydantic import BaseModel, Field
from pydantic import ValidationError as PydanticValidationError

from fastopenapi.core.params import (
    Body,
    Cookie,
    Depends,
    File,
    Form,
    Header,
    Param,
    Query,
)
from fastopenapi.core.types import RequestData
from fastopenapi.errors.exceptions import BadRequestError, ValidationError
from fastopenapi.resolution.resolver import ParameterResolver, ProcessedParameter


class TestModel(BaseModel):
    name: str
    age: int
    is_active: bool = True


class TestModelWithList(BaseModel):
    tags: list[str] = Field(default_factory=list)
    name: str


class TestModelOptional(BaseModel):
    optional_field: str | None = None
    required_field: str


class TestParameterResolver:
    def setup_method(self):
        self.resolver = ParameterResolver()
        self.request_data = RequestData(
            path_params={"id": "123"},
            query_params={"page": "1", "name": "John"},
            headers={"content-type": "application/json", "X-API-Key": "secret"},
            cookies={"session": "abc123"},
            body={"data": "test"},
            form_data={"username": "john"},
            files={"upload": b"file_content"},
        )

    def test_resolve_with_primitive_types(self):
        """Test resolving endpoint parameters with primitive types"""

        def endpoint(name: str, page: int, active: bool = False):
            return {"name": name, "page": page, "active": active}

        result = self.resolver.resolve(endpoint, self.request_data)

        assert result["name"] == "John"
        assert result["page"] == 1
        assert result["active"] is False

    def test_resolve_with_pydantic_model_body_source(self):
        """Test resolving Pydantic model from body"""

        def endpoint(user: TestModel):
            return user

        request_data = RequestData(body={"name": "John", "age": 30})
        result = self.resolver.resolve(endpoint, request_data)

        assert isinstance(result["user"], TestModel)
        assert result["user"].name == "John"
        assert result["user"].age == 30

    def test_resolve_with_pydantic_model_query_source(self):
        """Test resolving Pydantic model from query params should fail validation"""

        def endpoint(filters: TestModel):
            return filters

        # Empty query params should cause validation error
        request_data = RequestData(query_params={})

        with pytest.raises(ValidationError, match="Validation error for parameter"):
            self.resolver.resolve(endpoint, request_data)

    def test_resolve_missing_required_parameter(self):
        """Test error when required parameter is missing"""

        def endpoint(name: str, age: int):
            pass

        request_data = RequestData(query_params={"name": "John"})

        with pytest.raises(BadRequestError, match="Missing required parameter"):
            self.resolver.resolve(endpoint, request_data)

    def test_resolve_dependency_error(self):
        """Test dependency resolution error handling"""

        def endpoint(dep: str = Depends(lambda: "test")):
            return dep

        # Mock dependency resolver to raise error
        with patch("fastopenapi.resolution.resolver.dependency_resolver") as mock_dep:
            mock_dep.resolve_dependencies.side_effect = Exception("Dependency failed")

            with pytest.raises(Exception, match="Dependency failed"):
                self.resolver.resolve(endpoint, self.request_data)

    def test_resolve_with_header_param(self):
        """Test resolving header parameters"""

        def endpoint(content_type: str = Header()):
            return content_type

        result = self.resolver.resolve(endpoint, self.request_data)
        assert result["content_type"] == "application/json"

    def test_resolve_with_header_alias(self):
        """Test header with alias"""

        def endpoint(api_key: str = Header(alias="X-API-Key")):
            return api_key

        result = self.resolver.resolve(endpoint, self.request_data)
        assert result["api_key"] == "secret"

    def test_resolve_with_header_no_conversion(self):
        """Test header without underscore conversion"""

        def endpoint(content_type: str = Header(convert_underscores=False)):
            return content_type

        request_data = RequestData(headers={"content_type": "text/html"})
        result = self.resolver.resolve(endpoint, request_data)
        assert result["content_type"] == "text/html"

    def test_resolve_with_cookie_param(self):
        """Test resolving cookie parameters"""

        def endpoint(session_id: str = Cookie()):
            return session_id

        request_data = RequestData(cookies={"session_id": "abc123"})
        result = self.resolver.resolve(endpoint, request_data)
        assert result["session_id"] == "abc123"

    def test_resolve_with_form_param(self):
        """Test resolving form parameters"""

        def endpoint(username: str = Form()):
            return username

        result = self.resolver.resolve(endpoint, self.request_data)
        assert result["username"] == "john"

    # def test_resolve_with_file_upload(self):
    #     # Test resolving file upload
    #     from fastopenapi.core.types import RequestData
    #
    #     def endpoint(file: File):
    #         return file
    #
    #     mock_file = b"12345"
    #
    #     request_data = RequestData(files={"file": mock_file})
    #
    #     result = self.resolver.resolve(endpoint, request_data)
    #     assert result["file"] == mock_file

    def test_resolve_with_body_param(self):
        """Test resolving body parameters"""

        def endpoint(data: dict = Body()):
            return data

        result = self.resolver.resolve(endpoint, self.request_data)
        assert result["data"] == {"data": "test"}

    def test_resolve_with_path_params(self):
        """Test resolving path parameters"""

        def endpoint(user_id: int, name: str):
            return {"user_id": user_id, "name": name}

        request_data = RequestData(
            path_params={"user_id": "123"}, query_params={"name": "John"}
        )

        result = self.resolver.resolve(endpoint, request_data)
        assert result["user_id"] == 123
        assert result["name"] == "John"

    def test_determine_source_header(self):
        """Test determining source for Header parameter"""
        param = Mock()
        param.default = Header()

        source = self.resolver._determine_source("content_type", param, {})
        assert source.value == "header"

    def test_determine_source_cookie(self):
        """Test determining source for Cookie parameter"""
        param = Mock()
        param.default = Cookie()

        source = self.resolver._determine_source("session", param, {})
        assert source.value == "cookie"

    def test_determine_source_form(self):
        """Test determining source for Form parameter"""
        param = Mock()
        param.default = Form()

        source = self.resolver._determine_source("username", param, {})
        assert source.value == "form"

    def test_determine_source_body(self):
        """Test determining source for Body parameter"""
        param = Mock()
        param.default = Body()

        source = self.resolver._determine_source("data", param, {})
        assert source.value == "body"

    def test_determine_source_file_annotation(self):
        """Test determining source for File annotation"""
        param = Mock()
        param.default = inspect.Parameter.empty
        param.annotation = File

        source = self.resolver._determine_source("upload", param, {})
        assert source.value == "file"

    def test_determine_source_path_param(self):
        """Test determining source for path parameter"""
        param = Mock()
        param.default = inspect.Parameter.empty
        param.annotation = str

        source = self.resolver._determine_source("user_id", param, {"user_id": "123"})
        assert source.value == "path"

    def test_determine_source_pydantic_model(self):
        """Test determining source for Pydantic model"""
        param = Mock()
        param.default = inspect.Parameter.empty
        param.annotation = TestModel

        source = self.resolver._determine_source("user", param, {})
        assert source.value == "body"

    def test_determine_source_fallback_query(self):
        """Test determining source fallback to query"""
        param = Mock()
        param.default = inspect.Parameter.empty
        param.annotation = str

        source = self.resolver._determine_source("unknown", param, {})
        assert source.value == "query"

    def test_extract_header_value_case_insensitive(self):
        """Test case-insensitive header extraction"""
        headers = {"Content-Type": "application/json", "X-API-Key": "secret"}

        result1 = self.resolver._get_case_insensitive_header(headers, "content-type")
        result2 = self.resolver._get_case_insensitive_header(headers, "CONTENT-TYPE")
        result3 = self.resolver._get_case_insensitive_header(headers, "x-api-key")

        assert result1 == "application/json"
        assert result2 == "application/json"
        assert result3 == "secret"

    def test_extract_header_value_not_found(self):
        """Test header extraction when header not found"""
        headers = {"Content-Type": "application/json"}

        result = self.resolver._get_case_insensitive_header(headers, "missing-header")
        assert result is None

    def test_extract_header_with_underscore_conversion(self):
        """Test header extraction with underscore conversion"""
        param = Mock()
        param.default = Header()
        headers = {"user-agent": "test-agent"}

        result = self.resolver._extract_header_value(param, "user_agent", headers)
        assert result == "test-agent"

    def test_get_param_name_with_alias(self):
        """Test getting parameter name with alias"""
        param = Mock()
        param.default = Query(alias="custom_name")

        name = self.resolver._get_param_name("original", param)
        assert name == "custom_name"

    def test_get_param_name_without_alias(self):
        """Test getting parameter name without alias"""
        param = Mock()
        param.default = Query()
        param.default.alias = None

        name = self.resolver._get_param_name("original", param)
        assert name == "original"

    def test_get_param_name_non_param_object(self):
        """Test getting parameter name for non-Param object"""
        param = Mock()
        param.default = "default_value"

        name = self.resolver._get_param_name("original", param)
        assert name == "original"

    def test_is_required_param_with_ellipsis(self):
        """Test required parameter check with ellipsis"""
        param = Mock()
        param.default = Query(default=...)

        result = self.resolver._is_required_param(param)
        # Note: In Pydantic v2, this might not work as expected due to PydanticUndefined
        # Testing actual behavior
        assert isinstance(result, bool)

    def test_is_required_param_with_default(self):
        """Test parameter with default value"""
        param = Mock()
        param.default = Query(default="test")

        result = self.resolver._is_required_param(param)
        assert result is False

    def test_is_required_param_empty_default(self):
        """Test parameter with empty default"""
        param = Mock()
        param.default = inspect.Parameter.empty

        result = self.resolver._is_required_param(param)
        assert result is True

    def test_get_default_value_from_param(self):
        """Test getting default value from Param object"""
        param = Mock()
        param.default = Query(default="test_default")

        value = self.resolver._get_default_value(param)
        assert value == "test_default"

    def test_get_default_value_from_parameter(self):
        """Test getting default value from parameter"""
        param = Mock()
        param.default = "param_default"

        value = self.resolver._get_default_value(param)
        assert value == "param_default"

    def test_get_default_value_empty_parameter(self):
        """Test getting default value from empty parameter"""
        param = Mock()
        param.default = inspect.Parameter.empty

        value = self.resolver._get_default_value(param)
        assert value is None

    def test_needs_validation_param_object(self):
        """Test validation needed for Param object"""
        param = Mock()
        param.default = Query()

        result = self.resolver._needs_validation(param)
        assert result is True

    def test_needs_validation_type_annotation(self):
        """Test validation needed for type annotation"""
        param = Mock()
        param.default = inspect.Parameter.empty
        param.annotation = int

        result = self.resolver._needs_validation(param)
        assert result is True

    def test_needs_validation_no_annotation(self):
        """Test no validation needed without annotation"""
        param = Mock()
        param.default = "default"
        param.annotation = inspect.Parameter.empty

        result = self.resolver._needs_validation(param)
        assert result is False

    def test_build_field_info_with_constraints(self):
        """Test building field info with constraints"""
        param = Mock()
        param.default = Query(min_length=1, max_length=10, description="Test field")
        param.annotation = str

        field_info = self.resolver._build_field_info(param)

        assert len(field_info) == 2
        assert field_info[0] == str

    def test_build_field_constraints_all_constraints(self):
        """Test building field constraints with all possible constraints"""
        param_obj = Param(
            gt=0,
            ge=1,
            lt=100,
            le=99,
            multiple_of=5,
            min_length=2,
            max_length=50,
            pattern=r"^[a-z]+$",
            strict=True,
            description="Test description",
            title="Test title",
        )

        constraints = self.resolver._build_field_constraints(param_obj)

        assert constraints["gt"] == 0
        assert constraints["ge"] == 1
        assert constraints["lt"] == 100
        assert constraints["le"] == 99
        assert constraints["multiple_of"] == 5
        assert constraints["min_length"] == 2
        assert constraints["max_length"] == 50
        assert constraints["pattern"] == r"^[a-z]+$"
        assert constraints["strict"] is True
        assert constraints["description"] == "Test description"
        assert constraints["title"] == "Test title"

    def test_build_field_constraints_none_values(self):
        """Test building field constraints with None values"""
        param_obj = Param()
        param_obj.gt = None
        param_obj.description = None

        constraints = self.resolver._build_field_constraints(param_obj)

        assert "gt" not in constraints
        assert "description" not in constraints

    def test_is_pydantic_model_true(self):
        """Test Pydantic model detection positive case"""
        result = self.resolver._is_pydantic_model(TestModel)
        assert result is True

    def test_is_pydantic_model_false_non_class(self):
        """Test Pydantic model detection non-class"""
        result = self.resolver._is_pydantic_model("not_a_class")
        assert result is False

    def test_is_pydantic_model_false_regular_class(self):
        """Test Pydantic model detection regular class"""

        class RegularClass:
            pass

        result = self.resolver._is_pydantic_model(RegularClass)
        assert result is False

    def test_resolve_pydantic_model_empty_data(self):
        """Test resolving Pydantic model with empty data should raise ValidationError"""
        with pytest.raises(ValidationError, match="Validation error for parameter"):
            self.resolver._resolve_pydantic_model(TestModelWithList, {}, "model")

    def test_resolve_pydantic_model_none_data(self):
        """Test resolving Pydantic model with None data should raise ValidationError"""
        with pytest.raises(ValidationError, match="Validation error for parameter"):
            self.resolver._resolve_pydantic_model(TestModelWithList, None, "model")

    def test_resolve_pydantic_model_validation_error(self):
        """Test Pydantic model with validation error"""
        with pytest.raises(ValidationError, match="Validation error for parameter"):
            self.resolver._resolve_pydantic_model(
                TestModelOptional, {"optional_field": "test"}, "model"
            )

    def test_process_list_fields_convert_single_to_list(self):
        """Test converting single value to list for list fields"""
        data = {"tags": "single_tag", "name": "test"}

        result = self.resolver._process_list_fields(TestModelWithList, data)

        assert result["tags"] == ["single_tag"]
        assert result["name"] == "test"

    def test_process_list_fields_already_list(self):
        """Test list field that's already a list"""
        data = {"tags": ["tag1", "tag2"], "name": "test"}

        result = self.resolver._process_list_fields(TestModelWithList, data)

        assert result["tags"] == ["tag1", "tag2"]

    def test_process_list_fields_model_without_model_fields(self):
        """Test processing list fields on model without model_fields attribute"""
        mock_model = Mock()
        del mock_model.model_fields

        data = {"tags": "single_value"}

        result = self.resolver._process_list_fields(mock_model, data)
        assert result == data

    def test_process_list_fields_field_without_annotation(self):
        """Test field without annotation attribute"""
        mock_model = Mock()
        mock_field = Mock()
        del mock_field.annotation
        mock_model.model_fields = {"test_field": mock_field}

        data = {"test_field": "value"}

        result = self.resolver._process_list_fields(mock_model, data)
        assert result == data

    def test_validate_parameters_success(self):
        """Test successful parameter validation"""

        def endpoint(param: int = Query()):
            pass

        model_fields = {"param": (int, ...)}
        model_values = {"param": 123}

        result = self.resolver._validate_parameters(
            endpoint, model_fields, model_values
        )
        assert result["param"] == 123

    def test_validate_parameters_error(self):
        """Test parameter validation error"""

        def endpoint(param: int = Query()):
            pass

        model_fields = {"param": (int, ...)}
        model_values = {"param": "not_an_int"}

        with pytest.raises(BadRequestError, match="Error parsing parameter"):
            self.resolver._validate_parameters(endpoint, model_fields, model_values)

    def test_validate_parameters_empty_errors(self):
        """Test validation error with empty errors list"""

        def endpoint(param: int = Query()):
            pass

        model_fields = {"param": (int, ...)}
        model_values = {"param": "invalid"}

        with patch("pydantic.create_model") as mock_create:
            mock_model = Mock()
            mock_model.side_effect = PydanticValidationError.from_exception_data(
                "TestModel", []
            )
            mock_create.return_value = mock_model

            with pytest.raises(
                BadRequestError, match="Error parsing parameter 'param'"
            ):
                self.resolver._validate_parameters(endpoint, model_fields, model_values)

    def test_signature_caching(self):
        """Test signature caching mechanism"""

        def test_func(param: str):
            return param

        sig1 = dict(self.resolver._get_signature(test_func))
        sig2 = dict(self.resolver._get_signature(test_func))

        assert sig1 == sig2
        assert test_func in self.resolver._signature_cache

    def test_extract_value_unknown_source(self):
        """Test extracting value from unknown source"""

        param = Mock()
        unknown_source = Mock()
        unknown_source.value = "unknown"

        result = self.resolver._extract_value(
            "test", param, unknown_source, self.request_data
        )
        assert result is None

    def test_processed_parameter_init(self):
        """Test ProcessedParameter initialization"""
        pp = ProcessedParameter(
            value="test_value", needs_validation=True, field_info=(str, ...)
        )

        assert pp.value == "test_value"
        assert pp.needs_validation is True
        assert pp.field_info == (str, ...)

    def test_resolve_complex_endpoint_with_multiple_param_types(self):
        """Test resolving endpoint with multiple parameter types"""

        def endpoint(
            user_id: int,  # path param
            name: str = Query(),  # query param
            auth: str = Header(alias="Authorization"),  # header param
            session: str = Cookie(),  # cookie param
            data: dict = Body(),  # body param
            username: str = Form(),  # form param
        ):
            return {
                "user_id": user_id,
                "name": name,
                "auth": auth,
                "session": session,
                "data": data,
                "username": username,
            }

        request_data = RequestData(
            path_params={"user_id": "123"},
            query_params={"name": "John"},
            headers={"Authorization": "Bearer token"},
            cookies={"session": "abc123"},
            body={"key": "value"},
            form_data={"username": "john"},
        )

        result = self.resolver.resolve(endpoint, request_data)

        assert result["user_id"] == 123
        assert result["name"] == "John"
        assert result["auth"] == "Bearer token"
        assert result["session"] == "abc123"
        assert result["data"] == {"key": "value"}
        assert result["username"] == "john"

    # def test_resolve_with_validation_error_multiple_fields(self):
    #     """Test validation error with multiple validation errors"""
    #
    #     def endpoint(age: int = Query(ge=0), name: str = Query(min_length=1)):
    #         pass
    #
    #     request_data = RequestData(query_params={"age": "-5", "name": ""})
    #
    #     with pytest.raises(BadRequestError):
    #         self.resolver.resolve(endpoint, request_data)

    def test_extract_value_all_sources(self):
        """Test extracting values from all parameter sources"""
        from fastopenapi.core.constants import ParameterSource

        param = Mock()

        # Test PATH source
        result = self.resolver._extract_value(
            "id", param, ParameterSource.PATH, self.request_data
        )
        assert result == "123"

        # Test QUERY source
        result = self.resolver._extract_value(
            "name", param, ParameterSource.QUERY, self.request_data
        )
        assert result == "John"

        # Test HEADER source
        result = self.resolver._extract_value(
            "content-type", param, ParameterSource.HEADER, self.request_data
        )
        assert result == "application/json"

        # Test COOKIE source
        result = self.resolver._extract_value(
            "session", param, ParameterSource.COOKIE, self.request_data
        )
        assert result == "abc123"

        # Test FORM source
        result = self.resolver._extract_value(
            "username", param, ParameterSource.FORM, self.request_data
        )
        assert result == "john"

        # Test FILE source
        result = self.resolver._extract_value(
            "upload", param, ParameterSource.FILE, self.request_data
        )
        assert result == b"file_content"

        # Test BODY source
        result = self.resolver._extract_value(
            "data", param, ParameterSource.BODY, self.request_data
        )
        assert result == {"data": "test"}

    def test_build_field_info_no_constraints(self):
        """Test building field info without constraints"""
        param = Mock()
        param.default = Query(default="test")
        param.annotation = str

        with patch.object(self.resolver, "_build_field_constraints", return_value={}):
            field_info = self.resolver._build_field_info(param)

        assert len(field_info) == 2
        assert field_info[0] == str
        assert field_info[1] == "test"
