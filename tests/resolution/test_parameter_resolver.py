import inspect
from unittest.mock import MagicMock, Mock, patch

import pytest
from pydantic import BaseModel, Field
from pydantic_core import PydanticUndefined

from fastopenapi.core.constants import ParameterSource
from fastopenapi.core.params import (
    Body,
    Cookie,
    Depends,
    File,
    Form,
    Header,
    Query,
    Security,
)
from fastopenapi.core.types import RequestData
from fastopenapi.errors.exceptions import BadRequestError, ValidationError
from fastopenapi.resolution.resolver import ParameterResolver, ProcessedParameter


class TestProcessedParameter:
    """Tests for ProcessedParameter class"""

    def test_init_without_validation(self) -> None:
        """Test initialization without validation"""
        proc_param = ProcessedParameter(value=42, needs_validation=False)
        assert proc_param.value == 42
        assert proc_param.needs_validation is False
        assert proc_param.field_info is None

    def test_init_with_validation(self) -> None:
        """Test initialization with validation"""
        field_info = (int, ...)
        proc_param = ProcessedParameter(
            value=42, needs_validation=True, field_info=field_info
        )
        assert proc_param.value == 42
        assert proc_param.needs_validation is True
        assert proc_param.field_info == field_info


class TestParameterResolver:
    """Tests for ParameterResolver class"""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Clear caches before each test"""
        ParameterResolver._param_model_cache.clear()
        ParameterResolver._signature_cache.clear()

    @pytest.fixture
    def request_data(self) -> RequestData:
        """Base RequestData fixture for tests"""
        return RequestData(
            path_params={"user_id": "123"},
            query_params={"limit": "10", "offset": "0"},
            headers={"Content-Type": "application/json", "X-API-Key": "secret"},
            cookies={"session_id": "abc123"},
            body={"name": "Test User"},
            form_data={"username": "testuser"},
            files={"avatar": MagicMock()},
        )

    def test_get_signature_caching(self) -> None:
        """Test signature caching mechanism"""

        def test_endpoint(param1: int, param2: str) -> None:
            pass

        # First call - should cache
        result1 = ParameterResolver._get_signature(test_endpoint)
        assert test_endpoint in ParameterResolver._signature_cache

        # Second call - should use cache
        result2 = ParameterResolver._get_signature(test_endpoint)
        assert list(result1) == list(result2)

    def test_resolve_basic_parameters(self, request_data: RequestData) -> None:
        """Test resolving basic parameters from different sources"""

        def endpoint(user_id: str, limit: int) -> None:
            pass

        result = ParameterResolver.resolve(endpoint, request_data)
        assert result["user_id"] == "123"
        assert result["limit"] == 10

    def test_resolve_with_dependencies(self, request_data: RequestData) -> None:
        """Test resolving dependencies"""

        def dependency() -> str:
            return "dep_value"

        def endpoint(dep: str = Depends(dependency)) -> None:
            pass

        with patch.object(
            ParameterResolver,
            "_resolve_dependencies",
            return_value={"dep": "dep_value"},
        ):
            result = ParameterResolver.resolve(endpoint, request_data)
            assert result["dep"] == "dep_value"

    def test_resolve_dependencies_error_propagation(
        self, request_data: RequestData
    ) -> None:
        """Test that dependency errors are propagated"""

        def endpoint() -> None:
            pass

        with patch(
            "fastopenapi.resolution.resolver.dependency_resolver.resolve_dependencies",
            side_effect=RuntimeError("Dependency error"),
        ):
            with pytest.raises(RuntimeError, match="Dependency error"):
                ParameterResolver._resolve_dependencies(endpoint, request_data)

    def test_process_parameters_with_depends(self, request_data: RequestData) -> None:
        """Test that Depends parameters are skipped in processing"""

        def dependency() -> str:
            return "value"

        params_dict = {
            "dep": inspect.Parameter(
                "dep",
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=Depends(dependency),
            )
        }

        regular, model_fields, model_values = ParameterResolver._process_parameters(
            params_dict.items(), request_data
        )

        assert "dep" not in regular
        assert "dep" not in model_fields

    def test_process_parameters_with_security(self, request_data: RequestData) -> None:
        """Test that Security parameters are skipped in processing"""

        params_dict = {
            "token": inspect.Parameter(
                "token",
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=Security(lambda: "token"),
            )
        }

        regular, model_fields, model_values = ParameterResolver._process_parameters(
            params_dict.items(), request_data
        )

        assert "token" not in regular
        assert "token" not in model_fields

    def test_process_single_parameter_pydantic_model(
        self, request_data: RequestData
    ) -> None:
        """Test processing Pydantic model parameter"""

        class UserModel(BaseModel):
            name: str

        param = inspect.Parameter(
            "user", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=UserModel
        )

        result = ParameterResolver._process_single_parameter(
            "user", param, request_data
        )
        assert isinstance(result.value, UserModel)
        assert result.value.name == "Test User"
        assert result.needs_validation is False

    def test_process_single_parameter_missing_required(
        self, request_data: RequestData
    ) -> None:
        """Test missing required parameter raises error"""
        param = inspect.Parameter(
            "missing_param",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=str,
        )

        with pytest.raises(BadRequestError, match="Missing required parameter"):
            ParameterResolver._process_single_parameter(
                "missing_param", param, request_data
            )

    def test_process_single_parameter_with_default(
        self, request_data: RequestData
    ) -> None:
        """Test parameter with default value"""
        param = inspect.Parameter(
            "optional_param",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default="default_value",
            annotation=str,
        )

        result = ParameterResolver._process_single_parameter(
            "optional_param", param, request_data
        )
        assert result.value == "default_value"

    def test_determine_source_body(self) -> None:
        """Test source determination for Body"""
        param = inspect.Parameter(
            "data",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=Body(),
        )
        source = ParameterResolver._determine_source("data", param, {})
        assert source == ParameterSource.BODY

    def test_determine_source_file(self) -> None:
        """Test source determination for File"""
        param = inspect.Parameter(
            "upload",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=File(),
        )
        source = ParameterResolver._determine_source("upload", param, {})
        assert source == ParameterSource.FILE

    def test_determine_source_form(self) -> None:
        """Test source determination for Form"""
        param = inspect.Parameter(
            "username",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=Form(),
        )
        source = ParameterResolver._determine_source("username", param, {})
        assert source == ParameterSource.FORM

    def test_determine_source_query(self) -> None:
        """Test source determination for Query"""
        param = inspect.Parameter(
            "search",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=Query(),
        )
        source = ParameterResolver._determine_source("search", param, {})
        assert source == ParameterSource.QUERY

    def test_determine_source_header(self) -> None:
        """Test source determination for Header"""
        param = inspect.Parameter(
            "api_key",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=Header(),
        )
        source = ParameterResolver._determine_source("api_key", param, {})
        assert source == ParameterSource.HEADER

    def test_determine_source_cookie(self) -> None:
        """Test source determination for Cookie"""
        param = inspect.Parameter(
            "session",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=Cookie(),
        )
        source = ParameterResolver._determine_source("session", param, {})
        assert source == ParameterSource.COOKIE

    def test_determine_source_file_annotation(self) -> None:
        """Test source determination for File type annotation"""
        param = inspect.Parameter(
            "upload",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=File,
        )
        source = ParameterResolver._determine_source("upload", param, {})
        assert source == ParameterSource.FILE

    def test_determine_source_path(self) -> None:
        """Test source determination for path parameter"""
        param = inspect.Parameter(
            "user_id",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )
        source = ParameterResolver._determine_source("user_id", param, {"user_id": "1"})
        assert source == ParameterSource.PATH

    def test_determine_source_pydantic_model(self) -> None:
        """Test source determination for Pydantic model"""

        class Model(BaseModel):
            field: str

        param = inspect.Parameter(
            "data",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=Model,
        )
        source = ParameterResolver._determine_source("data", param, {})
        assert source == ParameterSource.BODY

    def test_determine_source_query_default(self) -> None:
        """Test source determination defaults to query"""
        param = inspect.Parameter(
            "search",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )
        source = ParameterResolver._determine_source("search", param, {})
        assert source == ParameterSource.QUERY

    def test_extract_value_path(self, request_data: RequestData) -> None:
        """Test extracting value from path parameters"""
        param = inspect.Parameter("user_id", inspect.Parameter.POSITIONAL_OR_KEYWORD)
        value = ParameterResolver._extract_value(
            "user_id", param, ParameterSource.PATH, request_data
        )
        assert value == "123"

    def test_extract_value_query(self, request_data: RequestData) -> None:
        """Test extracting value from query parameters"""
        param = inspect.Parameter("limit", inspect.Parameter.POSITIONAL_OR_KEYWORD)
        value = ParameterResolver._extract_value(
            "limit", param, ParameterSource.QUERY, request_data
        )
        assert value == "10"

    def test_extract_value_header(self, request_data: RequestData) -> None:
        """Test extracting value from headers"""
        param = inspect.Parameter(
            "x_api_key",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=Header(),
        )
        value = ParameterResolver._extract_value(
            "x_api_key", param, ParameterSource.HEADER, request_data
        )
        assert value == "secret"

    def test_extract_value_cookie(self, request_data: RequestData) -> None:
        """Test extracting value from cookies"""
        param = inspect.Parameter("session_id", inspect.Parameter.POSITIONAL_OR_KEYWORD)
        value = ParameterResolver._extract_value(
            "session_id", param, ParameterSource.COOKIE, request_data
        )
        assert value == "abc123"

    def test_extract_value_form(self, request_data: RequestData) -> None:
        """Test extracting value from form data"""
        param = inspect.Parameter("username", inspect.Parameter.POSITIONAL_OR_KEYWORD)
        value = ParameterResolver._extract_value(
            "username", param, ParameterSource.FORM, request_data
        )
        assert value == "testuser"

    def test_extract_value_file(self, request_data: RequestData) -> None:
        """Test extracting value from files"""
        param = inspect.Parameter("avatar", inspect.Parameter.POSITIONAL_OR_KEYWORD)
        value = ParameterResolver._extract_value(
            "avatar", param, ParameterSource.FILE, request_data
        )
        assert value is not None

    def test_extract_value_body(self, request_data: RequestData) -> None:
        """Test extracting value from body"""
        param = inspect.Parameter("data", inspect.Parameter.POSITIONAL_OR_KEYWORD)
        value = ParameterResolver._extract_value(
            "data", param, ParameterSource.BODY, request_data
        )
        assert value == {"name": "Test User"}

    def test_extract_value_unknown_source(self, request_data: RequestData) -> None:
        """Test extracting value from unknown source returns None"""
        param = inspect.Parameter("unknown", inspect.Parameter.POSITIONAL_OR_KEYWORD)
        value = ParameterResolver._extract_value(
            "unknown", param, "UNKNOWN_SOURCE", request_data
        )
        assert value is None

    def test_extract_header_value_with_alias(self) -> None:
        """Test extracting header with alias"""
        param = inspect.Parameter(
            "api_key",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=Header(alias="X-API-Key"),
        )
        headers = {"X-API-Key": "secret"}
        value = ParameterResolver._extract_header_value(param, "api_key", headers)
        assert value == "secret"

    def test_extract_header_value_with_underscore_conversion(self) -> None:
        """Test extracting header with underscore conversion"""
        param = inspect.Parameter(
            "api_key",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=Header(convert_underscores=True),
        )
        headers = {"Api-Key": "secret"}
        value = ParameterResolver._extract_header_value(param, "api_key", headers)
        assert value == "secret"

    def test_extract_header_value_without_underscore_conversion(self) -> None:
        """Test extracting header without underscore conversion"""
        param = inspect.Parameter(
            "api_key",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=Header(convert_underscores=False),
        )
        headers = {"api_key": "secret"}
        value = ParameterResolver._extract_header_value(param, "api_key", headers)
        assert value == "secret"

    def test_extract_header_value_without_header_default(self) -> None:
        """Test extracting header without Header default"""
        param = inspect.Parameter(
            "content_type",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )
        headers = {"Content-Type": "application/json"}
        value = ParameterResolver._extract_header_value(param, "content_type", headers)
        assert value == "application/json"

    def test_get_case_insensitive_header(self) -> None:
        """Test case-insensitive header retrieval"""
        headers = {"Content-Type": "application/json", "X-API-Key": "secret"}

        assert (
            ParameterResolver._get_case_insensitive_header(headers, "content-type")
            == "application/json"
        )
        assert (
            ParameterResolver._get_case_insensitive_header(headers, "CONTENT-TYPE")
            == "application/json"
        )
        assert (
            ParameterResolver._get_case_insensitive_header(headers, "x-api-key")
            == "secret"
        )
        assert (
            ParameterResolver._get_case_insensitive_header(headers, "missing") is None
        )

    def test_get_param_name_with_alias(self) -> None:
        """Test getting parameter name with alias"""
        param = inspect.Parameter(
            "internal_name",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=Query(alias="externalName"),
        )
        name = ParameterResolver._get_param_name("internal_name", param)
        assert name == "externalName"

    def test_get_param_name_without_alias(self) -> None:
        """Test getting parameter name without alias"""
        param = inspect.Parameter(
            "param_name",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )
        name = ParameterResolver._get_param_name("param_name", param)
        assert name == "param_name"

    def test_is_required_param_with_baseparam_ellipsis(self) -> None:
        """Test required parameter with BaseParam and ellipsis"""
        param = inspect.Parameter(
            "required",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=Query(default=...),
        )
        assert ParameterResolver._is_required_param(param) is True

    def test_is_required_param_with_baseparam_undefined(self) -> None:
        """Test required parameter with BaseParam and PydanticUndefined"""
        param = inspect.Parameter(
            "required",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=Query(default=PydanticUndefined),
        )
        assert ParameterResolver._is_required_param(param) is True

    def test_is_required_param_with_baseparam_default(self) -> None:
        """Test non-required parameter with BaseParam and default value"""
        param = inspect.Parameter(
            "optional",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=Query(default="default"),
        )
        assert ParameterResolver._is_required_param(param) is False

    def test_is_required_param_empty(self) -> None:
        """Test required parameter without default"""
        param = inspect.Parameter(
            "required",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )
        assert ParameterResolver._is_required_param(param) is True

    def test_is_required_param_with_default(self) -> None:
        """Test non-required parameter with default value"""
        param = inspect.Parameter(
            "optional",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default="default",
        )
        assert ParameterResolver._is_required_param(param) is False

    def test_get_default_value_from_baseparam(self) -> None:
        """Test getting default value from BaseParam"""
        param = inspect.Parameter(
            "param",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=Query(default="value"),
        )
        assert ParameterResolver._get_default_value(param) == "value"

    def test_get_default_value_from_baseparam_ellipsis(self) -> None:
        """Test getting default value from BaseParam with ellipsis"""
        param = inspect.Parameter(
            "param",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=Query(default=...),
        )
        assert ParameterResolver._get_default_value(param) is None

    def test_get_default_value_from_baseparam_undefined(self) -> None:
        """Test getting default value from BaseParam with PydanticUndefined"""
        param = inspect.Parameter(
            "param",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=Query(default=PydanticUndefined),
        )
        assert ParameterResolver._get_default_value(param) is None

    def test_get_default_value_from_parameter(self) -> None:
        """Test getting default value from parameter"""
        param = inspect.Parameter(
            "param",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default="default",
        )
        assert ParameterResolver._get_default_value(param) == "default"

    def test_get_default_value_none(self) -> None:
        """Test getting default value when none exists"""
        param = inspect.Parameter(
            "param",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )
        assert ParameterResolver._get_default_value(param) is None

    def test_needs_validation_with_baseparam(self) -> None:
        """Test validation needed for BaseParam"""
        param = inspect.Parameter(
            "param",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=Query(),
        )
        assert ParameterResolver._needs_validation(param) is True

    def test_needs_validation_with_annotation(self) -> None:
        """Test validation needed for annotated parameter"""
        param = inspect.Parameter(
            "param",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=int,
        )
        assert ParameterResolver._needs_validation(param) is True

    def test_needs_validation_without_annotation(self) -> None:
        """Test validation not needed without annotation"""
        param = inspect.Parameter(
            "param",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )
        assert ParameterResolver._needs_validation(param) is False

    def test_build_field_info_with_constraints(self) -> None:
        """Test building field info with constraints"""
        param = inspect.Parameter(
            "param",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=int,
            default=Query(default=10, gt=0, le=100),
        )

        annotation, field = ParameterResolver._build_field_info(param)
        assert annotation == int
        assert isinstance(field, type(Field()))

    def test_build_field_info_without_constraints(self) -> None:
        """Test building field info without constraints"""
        param = inspect.Parameter(
            "param",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=str,
            default=Query(default="value"),
        )

        with patch.object(
            ParameterResolver, "_build_field_constraints", return_value={}
        ):
            annotation, default = ParameterResolver._build_field_info(param)
            assert annotation == str
            assert default == "value"

    def test_build_field_info_required(self) -> None:
        """Test building field info for required parameter"""
        param = inspect.Parameter(
            "param",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=str,
            default=Query(default=...),
        )

        with patch.object(
            ParameterResolver, "_build_field_constraints", return_value={}
        ):
            annotation, default = ParameterResolver._build_field_info(param)
            assert annotation == str
            # In Pydantic v2, ... may be converted to PydanticUndefined
            assert default is ... or default is PydanticUndefined

    def test_process_numeric_constraints_missing_attribute(self) -> None:
        """Test processing numeric constraint when attribute is missing"""
        constraint = Mock(spec=[])  # Empty spec = no attributes
        type(constraint).__name__ = "Gt"  # Constraint type matches mapping
        field_kwargs = {}

        # Should not raise error, just skip the constraint
        ParameterResolver._process_numeric_constraints(constraint, "Gt", field_kwargs)

        # field_kwargs should remain empty since hasattr returned False
        assert field_kwargs == {}

    def test_process_numeric_constraints_gt(self) -> None:
        """Test processing Gt constraint"""
        constraint = Mock()
        constraint.gt = 0
        field_kwargs = {}

        ParameterResolver._process_numeric_constraints(constraint, "Gt", field_kwargs)
        assert field_kwargs["gt"] == 0

    def test_process_numeric_constraints_ge(self) -> None:
        """Test processing Ge constraint"""
        constraint = Mock()
        constraint.ge = 0
        field_kwargs = {}

        ParameterResolver._process_numeric_constraints(constraint, "Ge", field_kwargs)
        assert field_kwargs["ge"] == 0

    def test_process_numeric_constraints_lt(self) -> None:
        """Test processing Lt constraint"""
        constraint = Mock()
        constraint.lt = 100
        field_kwargs = {}

        ParameterResolver._process_numeric_constraints(constraint, "Lt", field_kwargs)
        assert field_kwargs["lt"] == 100

    def test_process_numeric_constraints_le(self) -> None:
        """Test processing Le constraint"""
        constraint = Mock()
        constraint.le = 100
        field_kwargs = {}

        ParameterResolver._process_numeric_constraints(constraint, "Le", field_kwargs)
        assert field_kwargs["le"] == 100

    def test_process_numeric_constraints_multiple_of(self) -> None:
        """Test processing MultipleOf constraint"""
        constraint = Mock()
        constraint.multiple_of = 5
        field_kwargs = {}

        ParameterResolver._process_numeric_constraints(
            constraint, "MultipleOf", field_kwargs
        )
        assert field_kwargs["multiple_of"] == 5

    def test_process_numeric_constraints_unknown(self) -> None:
        """Test processing unknown numeric constraint"""
        constraint = Mock()
        field_kwargs = {}

        ParameterResolver._process_numeric_constraints(
            constraint, "Unknown", field_kwargs
        )
        assert field_kwargs == {}

    def test_process_string_constraints_min_len(self) -> None:
        """Test processing MinLen constraint"""
        constraint = Mock()
        constraint.min_length = 5
        field_kwargs = {}

        ParameterResolver._process_string_constraints(
            constraint, "MinLen", field_kwargs
        )
        assert field_kwargs["min_length"] == 5

    def test_process_string_constraints_max_len(self) -> None:
        """Test processing MaxLen constraint"""
        constraint = Mock()
        constraint.max_length = 100
        field_kwargs = {}

        ParameterResolver._process_string_constraints(
            constraint, "MaxLen", field_kwargs
        )
        assert field_kwargs["max_length"] == 100

    def test_process_string_constraints_unknown(self) -> None:
        """Test processing unknown string constraint"""
        constraint = Mock()
        field_kwargs = {}

        ParameterResolver._process_string_constraints(
            constraint, "Unknown", field_kwargs
        )
        assert field_kwargs == {}

    def test_process_pattern_constraint(self) -> None:
        """Test processing pattern constraint"""
        constraint = Mock()
        constraint.pattern = r"^\d+$"
        field_kwargs = {}

        ParameterResolver._process_pattern_constraint(constraint, field_kwargs)
        assert field_kwargs["pattern"] == r"^\d+$"

    def test_process_pattern_constraint_missing(self) -> None:
        """Test processing pattern constraint when attribute missing"""
        constraint = Mock(spec=[])
        field_kwargs = {}

        ParameterResolver._process_pattern_constraint(constraint, field_kwargs)
        assert field_kwargs == {}

    def test_process_strict_mode(self) -> None:
        """Test processing strict mode constraint"""
        constraint = Mock()
        constraint.strict = True
        field_kwargs = {}

        ParameterResolver._process_strict_mode(constraint, "Strict", field_kwargs)
        assert field_kwargs["strict"] is True

    def test_process_strict_mode_non_strict_type(self) -> None:
        """Test processing non-Strict constraint type"""
        constraint = Mock()
        field_kwargs = {}

        ParameterResolver._process_strict_mode(constraint, "Other", field_kwargs)
        assert field_kwargs == {}

    def test_process_float_decimal_constraints(self) -> None:
        """Test processing float/decimal constraints"""
        constraint = Mock()
        constraint.allow_inf_nan = True
        constraint.max_digits = 10
        constraint.decimal_places = 2
        field_kwargs = {}

        ParameterResolver._process_float_decimal_constraints(constraint, field_kwargs)
        assert field_kwargs["allow_inf_nan"] is True
        assert field_kwargs["max_digits"] == 10
        assert field_kwargs["decimal_places"] == 2

    def test_process_float_decimal_constraints_partial(self) -> None:
        """Test processing float/decimal constraints with missing attributes"""
        constraint = Mock(spec=["max_digits"])
        constraint.max_digits = 5
        field_kwargs = {}

        ParameterResolver._process_float_decimal_constraints(constraint, field_kwargs)
        assert field_kwargs["max_digits"] == 5
        assert "allow_inf_nan" not in field_kwargs

    def test_process_metadata(self) -> None:
        """Test processing metadata fields"""
        param_obj = Mock()
        param_obj.description = "Test description"
        param_obj.title = "Test Title"
        field_kwargs = {}

        ParameterResolver._process_metadata(param_obj, field_kwargs)
        assert field_kwargs["description"] == "Test description"
        assert field_kwargs["title"] == "Test Title"

    def test_process_metadata_partial(self) -> None:
        """Test processing metadata with None values"""
        param_obj = Mock()
        param_obj.description = None
        param_obj.title = "Test Title"
        field_kwargs = {}

        ParameterResolver._process_metadata(param_obj, field_kwargs)
        assert "description" not in field_kwargs
        assert field_kwargs["title"] == "Test Title"

    def test_build_field_constraints_comprehensive(self) -> None:
        """Test building field constraints with all constraint types"""

        # Create mock constraints
        gt_constraint = Mock()
        gt_constraint.gt = 0
        type(gt_constraint).__name__ = "Gt"

        min_len_constraint = Mock()
        min_len_constraint.min_length = 5
        type(min_len_constraint).__name__ = "MinLen"

        pattern_constraint = Mock()
        pattern_constraint.pattern = r"^\w+$"
        type(pattern_constraint).__name__ = "Pattern"

        param_obj = Mock()
        param_obj.metadata = [gt_constraint, min_len_constraint, pattern_constraint]
        param_obj.description = "Test param"
        param_obj.title = "Test"

        result = ParameterResolver._build_field_constraints(param_obj)

        assert result["gt"] == 0
        assert result["min_length"] == 5
        assert result["pattern"] == r"^\w+$"
        assert result["description"] == "Test param"
        assert result["title"] == "Test"

    def test_is_pydantic_model_true(self) -> None:
        """Test identifying Pydantic model"""

        class TestModel(BaseModel):
            field: str

        assert ParameterResolver._is_pydantic_model(TestModel) is True

    def test_is_pydantic_model_false(self) -> None:
        """Test identifying non-Pydantic class"""

        class RegularClass:
            pass

        assert ParameterResolver._is_pydantic_model(RegularClass) is False

    def test_is_pydantic_model_not_type(self) -> None:
        """Test identifying non-type value"""
        assert ParameterResolver._is_pydantic_model("not a type") is False
        assert ParameterResolver._is_pydantic_model(42) is False

    def test_resolve_pydantic_model_success(self) -> None:
        """Test successful Pydantic model resolution"""

        class UserModel(BaseModel):
            name: str
            age: int

        data = {"name": "John", "age": 30}
        result = ParameterResolver._resolve_pydantic_model(UserModel, data, "user")

        assert isinstance(result, UserModel)
        assert result.name == "John"
        assert result.age == 30

    def test_resolve_pydantic_model_empty_data(self) -> None:
        """Test Pydantic model resolution with empty data"""

        class UserModel(BaseModel):
            name: str = "default"

        result = ParameterResolver._resolve_pydantic_model(UserModel, None, "user")
        assert isinstance(result, UserModel)
        assert result.name == "default"

    def test_resolve_pydantic_model_validation_error(self) -> None:
        """Test Pydantic model resolution with validation error"""

        class UserModel(BaseModel):
            age: int

        data = {"age": "not a number"}

        with pytest.raises(ValidationError, match="Validation error for parameter"):
            ParameterResolver._resolve_pydantic_model(UserModel, data, "user")

    def test_process_list_fields(self) -> None:
        """Test processing list fields in Pydantic model"""

        class ModelWithList(BaseModel):
            tags: list[str]
            name: str

        data = {"tags": "single_tag", "name": "test"}
        result = ParameterResolver._process_list_fields(ModelWithList, data)

        assert result["tags"] == ["single_tag"]
        assert result["name"] == "test"

    def test_process_list_fields_already_list(self) -> None:
        """Test processing list fields when value is already a list"""

        class ModelWithList(BaseModel):
            tags: list[str]

        data = {"tags": ["tag1", "tag2"]}
        result = ParameterResolver._process_list_fields(ModelWithList, data)

        assert result["tags"] == ["tag1", "tag2"]

    def test_process_list_fields_no_model_fields(self) -> None:
        """Test processing list fields for model without model_fields"""

        class OldStyleModel:
            pass

        data = {"field": "value"}
        result = ParameterResolver._process_list_fields(OldStyleModel, data)

        assert result == data

    def test_get_or_create_validation_model_caching(self) -> None:
        """Test validation model caching"""

        def endpoint(param1: int, param2: str) -> None:
            pass

        # Use simple tuples to ensure consistent cache keys
        model_fields = {
            "param1": (int, ...),
            "param2": (str, "default"),
        }

        # Clear cache before test
        ParameterResolver._param_model_cache.clear()

        # First call - creates model
        ParameterResolver._get_or_create_validation_model(endpoint, model_fields)
        cache_size_after_first = len(ParameterResolver._param_model_cache)

        # Second call - should use cache (cache size shouldn't increase)
        ParameterResolver._get_or_create_validation_model(endpoint, model_fields)
        cache_size_after_second = len(ParameterResolver._param_model_cache)

        # Verify caching worked
        assert cache_size_after_first == 1
        assert cache_size_after_second == 1

    def test_get_or_create_validation_model_different_fields(self) -> None:
        """Test validation model creation for different field sets"""

        def endpoint(param: int) -> None:
            pass

        fields1 = {"param1": (int, ...)}
        fields2 = {"param2": (str, ...)}

        model1 = ParameterResolver._get_or_create_validation_model(endpoint, fields1)
        model2 = ParameterResolver._get_or_create_validation_model(endpoint, fields2)

        assert model1 is not model2
        assert len(ParameterResolver._param_model_cache) == 2

    def test_validate_parameters_success(self) -> None:
        """Test successful parameter validation"""

        def endpoint(age: int, name: str) -> None:
            pass

        model_fields = {"age": (int, ...), "name": (str, ...)}
        model_values = {"age": 25, "name": "John"}

        result = ParameterResolver._validate_parameters(
            endpoint, model_fields, model_values
        )

        assert result["age"] == 25
        assert result["name"] == "John"

    def test_validate_parameters_type_coercion(self) -> None:
        """Test parameter validation with type coercion"""

        def endpoint(age: int) -> None:
            pass

        model_fields = {"age": (int, ...)}
        model_values = {"age": "25"}

        result = ParameterResolver._validate_parameters(
            endpoint, model_fields, model_values
        )

        assert result["age"] == 25
        assert isinstance(result["age"], int)

    def test_validate_parameters_validation_error(self) -> None:
        """Test parameter validation error"""

        def endpoint(age: int) -> None:
            pass

        model_fields = {"age": (int, ...)}
        model_values = {"age": "not a number"}

        with pytest.raises(BadRequestError, match="Error parsing parameter"):
            ParameterResolver._validate_parameters(endpoint, model_fields, model_values)

    def test_validate_parameters_empty_errors_list(self) -> None:
        """Test parameter validation with empty errors list"""

        def endpoint(param: int) -> None:
            pass

        model_fields = {"param": (int, ...)}
        model_values = {"param": "invalid"}

        with patch("fastopenapi.resolution.resolver.create_model") as mock_create:
            mock_model = Mock()
            mock_instance = Mock()

            # Create PydanticValidationError with empty errors list
            from pydantic import ValidationError as PydanticValidationError

            validation_error = PydanticValidationError.from_exception_data(
                "TestModel", []
            )

            mock_model.return_value = mock_instance
            mock_instance.model_dump.side_effect = validation_error
            mock_create.return_value = mock_model

            with pytest.raises(BadRequestError, match="Parameter validation failed"):
                ParameterResolver._validate_parameters(
                    endpoint, model_fields, model_values
                )

    def test_resolve_integration_all_sources(self) -> None:
        """Integration test with parameters from all sources"""

        def endpoint(
            user_id: str,
            limit: int,
            x_api_key: str = Header(),
            session_id: str = Cookie(),
        ) -> None:
            pass

        request_data = RequestData(
            path_params={"user_id": "123"},
            query_params={"limit": "50"},
            headers={"X-API-Key": "secret"},
            cookies={"session_id": "abc"},
            body={},
            form_data={},
            files={},
        )

        result = ParameterResolver.resolve(endpoint, request_data)

        assert result["user_id"] == "123"
        assert result["limit"] == 50
        assert result["x_api_key"] == "secret"
        assert result["session_id"] == "abc"

    def test_resolve_integration_pydantic_body(self) -> None:
        """Integration test with Pydantic model in body"""

        class UserCreate(BaseModel):
            name: str
            email: str

        def endpoint(user: UserCreate) -> None:
            pass

        request_data = RequestData(
            path_params={},
            query_params={},
            headers={},
            cookies={},
            body={"name": "John", "email": "john@example.com"},
            form_data={},
            files={},
        )

        result = ParameterResolver.resolve(endpoint, request_data)

        assert isinstance(result["user"], UserCreate)
        assert result["user"].name == "John"
        assert result["user"].email == "john@example.com"

    def test_resolve_integration_with_defaults(self) -> None:
        """Integration test with default values"""

        def endpoint(
            required: str,
            optional: str = "default_value",
            limit: int = 10,
        ) -> None:
            pass

        request_data = RequestData(
            path_params={},
            query_params={"required": "value"},
            headers={},
            cookies={},
            body={},
            form_data={},
            files={},
        )

        result = ParameterResolver.resolve(endpoint, request_data)

        assert result["required"] == "value"
        assert result["optional"] == "default_value"
        assert result["limit"] == 10

    def test_resolve_integration_complex_validation(self) -> None:
        """Integration test with complex validation using Query"""

        def endpoint(
            age: int = Query(ge=0, le=150),
            name: str = Query(min_length=2, max_length=50),
        ) -> None:
            pass

        request_data = RequestData(
            path_params={},
            query_params={"age": "25", "name": "John"},
            headers={},
            cookies={},
            body={},
            form_data={},
            files={},
        )

        result = ParameterResolver.resolve(endpoint, request_data)

        assert result["age"] == 25
        assert result["name"] == "John"
