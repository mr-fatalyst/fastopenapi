import typing

import pytest
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from fastopenapi.core.constants import ParameterSource
from fastopenapi.core.params import (
    Body,
    Cookie,
    Depends,
    File,
    Form,
    Header,
    ItemId,
    LimitedStr,
    LimitQuery,
    NonEmptyStr,
    NonNegativeInt,
    OffsetQuery,
    PageQuery,
    Param,
    Path,
    PositiveFloat,
    PositiveInt,
    Query,
    Security,
    UserId,
)


class TestParam:
    """Test base Param class"""

    def test_param_init_minimal(self):
        """Test Param initialization with minimal parameters"""
        param = Param()
        assert param.default is PydanticUndefined
        assert param.alias is None
        assert param.title is None
        assert param.description is None
        assert param.examples is None
        assert param.include_in_schema is True

    def test_param_init_full(self):
        """Test Param initialization with all parameters"""
        examples = ["example1", "example2"]
        json_schema_extra = {"custom": "field"}

        param = Param(
            default="test_default",
            alias="test_alias",
            title="Test Title",
            description="Test description",
            gt=0,
            ge=1,
            lt=100,
            le=99,
            min_length=5,
            max_length=50,
            pattern=r"^test",
            strict=True,
            multiple_of=2,
            allow_inf_nan=False,
            max_digits=10,
            decimal_places=2,
            examples=examples,
            deprecated=True,
            include_in_schema=False,
            json_schema_extra=json_schema_extra,
            custom_field="custom_value",
        )

        assert param.default == "test_default"
        assert param.alias == "test_alias"
        assert param.title == "Test Title"
        assert param.description == "Test description"
        assert param.examples == examples
        assert param.deprecated is True
        assert param.include_in_schema is False
        assert param.json_schema_extra == json_schema_extra

    def test_param_none_values_filtered(self):
        """Test that None values are filtered out except default"""
        param = Param(
            default=None,
            alias=None,
            title=None,
            description=None,
            gt=None,
        )

        assert param.default is None

    def test_param_repr(self):
        """Test Param string representation"""
        param = Param("default_value")
        assert repr(param) == "Param(default_value)"


class TestQuery:
    """Test Query parameter class"""

    def test_query_in_source(self):
        """Test Query parameter source"""
        query = Query()
        assert query.in_ == ParameterSource.QUERY

    def test_query_init_minimal(self):
        """Test Query initialization with minimal parameters"""
        query = Query()
        assert query.default is None

    def test_query_init_with_default(self):
        """Test Query initialization with default value"""
        query = Query("default_value")
        assert query.default == "default_value"

    def test_query_init_full_constraints(self):
        """Test Query with full constraint set"""
        query = Query(
            default="test",
            alias="q",
            title="Query Parameter",
            description="A test query parameter",
            min_length=1,
            max_length=100,
            pattern=r"^\w+$",
            examples=["example1", "example2"],
        )

        assert query.default == "test"
        assert query.alias == "q"
        assert query.title == "Query Parameter"
        assert query.description == "A test query parameter"
        assert query.examples == ["example1", "example2"]


class TestPath:
    """Test Path parameter class"""

    def test_path_in_source(self):
        """Test Path parameter source"""
        path = Path()
        assert path.in_ == ParameterSource.PATH

    def test_path_init_minimal(self):
        """Test Path initialization with minimal parameters"""
        path = Path()
        assert path.default is PydanticUndefined  # Changed to PydanticUndefined

    def test_path_cannot_have_default(self):
        """Test Path parameters cannot have default values"""
        with pytest.raises(
            ValueError, match="Path parameters cannot have a default value"
        ):
            Path(default="some_default")

    def test_path_with_ellipsis_default(self):
        """Test Path with ellipsis default (allowed)"""
        path = Path(default=...)
        assert (
            path.default is PydanticUndefined
        )  # Pydantic converts ... to PydanticUndefined

    def test_path_init_with_constraints(self):
        """Test Path with validation constraints"""
        path = Path(
            alias="item_id",
            title="Item ID",
            description="The ID of the item",
            gt=0,
            le=999999,
            examples=[1, 123, 456],
        )

        assert path.alias == "item_id"
        assert path.title == "Item ID"
        assert path.description == "The ID of the item"
        assert path.examples == [1, 123, 456]


class TestHeader:
    """Test Header parameter class"""

    def test_header_in_source(self):
        """Test Header parameter source"""
        header = Header()
        assert header.in_ == ParameterSource.HEADER

    def test_header_init_minimal(self):
        """Test Header initialization with minimal parameters"""
        header = Header()
        assert header.default is None
        assert header.convert_underscores is True

    def test_header_convert_underscores_disabled(self):
        """Test Header with underscore conversion disabled"""
        header = Header(convert_underscores=False)
        assert header.convert_underscores is False

    def test_header_init_full(self):
        """Test Header with full parameter set"""
        header = Header(
            default="application/json",
            alias="Content-Type",
            convert_underscores=False,
            title="Content Type",
            description="The content type of the request",
            examples=["application/json", "text/html"],
        )

        assert header.default == "application/json"
        assert header.alias == "Content-Type"
        assert header.convert_underscores is False
        assert header.title == "Content Type"
        assert header.description == "The content type of the request"
        assert header.examples == ["application/json", "text/html"]


class TestCookie:
    """Test Cookie parameter class"""

    def test_cookie_in_source(self):
        """Test Cookie parameter source"""
        cookie = Cookie()
        assert cookie.in_ == ParameterSource.COOKIE

    def test_cookie_init_minimal(self):
        """Test Cookie initialization with minimal parameters"""
        cookie = Cookie()
        assert cookie.default is None

    def test_cookie_init_with_constraints(self):
        """Test Cookie with validation constraints"""
        cookie = Cookie(
            default="session123",
            alias="sessionid",
            title="Session ID",
            description="User session identifier",
            min_length=8,
            max_length=32,
            pattern=r"^session\d+$",
        )

        assert cookie.default == "session123"
        assert cookie.alias == "sessionid"
        assert cookie.title == "Session ID"
        assert cookie.description == "User session identifier"


class TestBody:
    """Test Body parameter class"""

    def test_body_init_minimal(self):
        """Test Body initialization with minimal parameters"""
        body = Body()
        assert body.default is None
        assert body.embed is None
        assert body.media_type == "application/json"
        assert body.examples is None
        assert body.include_in_schema is True

    def test_body_init_full(self):
        """Test Body with full parameter set"""
        examples = [{"key": "value1"}, {"key": "value2"}]
        json_schema_extra = {"custom": "body_field"}

        body = Body(
            default={"default": "data"},
            embed=True,
            media_type="application/xml",
            alias="request_body",
            title="Request Body",
            description="The request body data",
            examples=examples,
            deprecated=True,
            include_in_schema=False,
            json_schema_extra=json_schema_extra,
        )

        assert body.default == {"default": "data"}
        assert body.embed is True
        assert body.media_type == "application/xml"
        assert body.alias == "request_body"
        assert body.title == "Request Body"
        assert body.description == "The request body data"
        assert body.examples == examples
        assert body.deprecated is True
        assert body.include_in_schema is False
        assert body.json_schema_extra == json_schema_extra

    def test_body_repr(self):
        """Test Body string representation"""
        body = Body({"test": "data"})
        assert repr(body) == "Body({'test': 'data'})"


class TestForm:
    """Test Form parameter class"""

    def test_form_inherits_from_body(self):
        """Test Form inherits from Body"""
        assert issubclass(Form, Body)

    def test_form_init_minimal(self):
        """Test Form initialization with minimal parameters"""
        form = Form()
        assert form.default is None
        assert form.media_type == "application/x-www-form-urlencoded"

    def test_form_init_with_custom_media_type(self):
        """Test Form with custom media type"""
        form = Form(
            default="form_data",
            media_type="custom/form-type",
            alias="form_field",
            title="Form Field",
        )

        assert form.default == "form_data"
        assert form.media_type == "custom/form-type"
        assert form.alias == "form_field"
        assert form.title == "Form Field"

    def test_form_with_constraints(self):
        """Test Form with validation constraints"""
        form = Form(
            default="test_value",
            min_length=5,
            max_length=100,
            pattern=r"^\w+$",
            examples=["example1", "example2"],
        )

        assert form.default == "test_value"
        assert form.examples == ["example1", "example2"]


class TestFile:
    """Test File parameter class"""

    def test_file_inherits_from_form(self):
        """Test File inherits from Form"""
        assert issubclass(File, Form)

    def test_file_init_minimal(self):
        """Test File initialization with minimal parameters"""
        file = File()
        assert file.default is None
        assert file.media_type == "multipart/form-data"

    def test_file_init_with_parameters(self):
        """Test File with custom parameters"""
        file = File(
            alias="upload_file",
            title="Upload File",
            description="File to upload",
            examples=["file1.txt", "file2.pdf"],
        )

        assert file.default is None
        assert file.media_type == "multipart/form-data"
        assert file.alias == "upload_file"
        assert file.title == "Upload File"
        assert file.description == "File to upload"
        assert file.examples == ["file1.txt", "file2.pdf"]


class TestDepends:
    """Test Depends class"""

    def test_depends_init_minimal(self):
        """Test Depends initialization with minimal parameters"""
        depends = Depends()
        assert depends.dependency is None

    def test_depends_init_with_function(self):
        """Test Depends with dependency function"""

        def test_dependency():
            return "test_result"

        depends = Depends(test_dependency)
        assert depends.dependency is test_dependency

    def test_depends_repr_with_function(self):
        """Test Depends string representation with function"""

        def test_dependency():
            return "test_result"

        depends = Depends(test_dependency)
        assert repr(depends) == "Depends(test_dependency)"

    def test_depends_repr_with_class(self):
        """Test Depends string representation with class"""

        class TestClass:
            pass

        depends = Depends(TestClass)
        assert repr(depends) == "Depends(TestClass)"

    def test_depends_repr_none_dependency(self):
        """Test Depends string representation with None dependency"""
        depends = Depends()
        assert repr(depends) == "Depends(NoneType)"


class TestSecurity:
    """Test Security class"""

    def test_security_inherits_from_depends(self):
        """Test Security inherits from Depends"""
        assert issubclass(Security, Depends)

    def test_security_init_minimal(self):
        """Test Security initialization with minimal parameters"""
        security = Security()
        assert security.dependency is None
        assert security.scopes == []

    def test_security_init_with_function(self):
        """Test Security with dependency function"""

        def auth_dependency():
            return {"user": "john"}

        security = Security(auth_dependency)
        assert security.dependency is auth_dependency
        assert security.scopes == []

    def test_security_init_with_scopes(self):
        """Test Security with scopes"""

        def auth_dependency():
            return {"user": "john"}

        scopes = ["read", "write", "admin"]
        security = Security(auth_dependency, scopes=scopes)
        assert security.dependency is auth_dependency
        assert security.scopes == scopes

    def test_security_init_full(self):
        """Test Security with all parameters"""

        def auth_dependency():
            return {"user": "john"}

        scopes = ["read", "write"]
        security = Security(auth_dependency, scopes=scopes)
        assert security.dependency is auth_dependency
        assert security.scopes == scopes

    def test_security_scopes_none_to_empty_list(self):
        """Test Security converts None scopes to empty list"""
        security = Security(scopes=None)
        assert security.scopes == []

    def test_security_scopes_tuple_to_list(self):
        """Test Security converts tuple scopes to list"""
        scopes = ("read", "write", "admin")
        security = Security(scopes=scopes)
        assert security.scopes == ["read", "write", "admin"]


class TestPredefinedTypes:
    """Test pre-defined validation types"""

    def test_positive_int_type(self):
        """Test PositiveInt type definition"""
        origin = typing.get_origin(PositiveInt)
        args = typing.get_args(PositiveInt)

        assert origin is typing.Annotated
        assert args[0] is int

    def test_non_negative_int_type(self):
        """Test NonNegativeInt type definition"""
        origin = typing.get_origin(NonNegativeInt)
        args = typing.get_args(NonNegativeInt)

        assert origin is typing.Annotated
        assert args[0] is int

    def test_positive_float_type(self):
        """Test PositiveFloat type definition"""
        origin = typing.get_origin(PositiveFloat)
        args = typing.get_args(PositiveFloat)

        assert origin is typing.Annotated
        assert args[0] is float

    def test_non_empty_str_type(self):
        """Test NonEmptyStr type definition"""
        origin = typing.get_origin(NonEmptyStr)
        args = typing.get_args(NonEmptyStr)

        assert origin is typing.Annotated
        assert args[0] is str

    def test_limited_str_type(self):
        """Test LimitedStr type definition"""
        origin = typing.get_origin(LimitedStr)
        args = typing.get_args(LimitedStr)

        assert origin is typing.Annotated
        assert args[0] is str

    def test_user_id_type(self):
        """Test UserId type definition"""
        origin = typing.get_origin(UserId)
        args = typing.get_args(UserId)

        assert origin is typing.Annotated
        assert args[0] is int
        assert isinstance(args[1], Path)

    def test_item_id_type(self):
        """Test ItemId type definition"""
        origin = typing.get_origin(ItemId)
        args = typing.get_args(ItemId)

        assert origin is typing.Annotated
        assert args[0] is int
        assert isinstance(args[1], Path)

    def test_page_query_type(self):
        """Test PageQuery type definition"""
        origin = typing.get_origin(PageQuery)
        args = typing.get_args(PageQuery)

        assert origin is typing.Annotated
        assert args[0] is int
        assert isinstance(args[1], Query)

    def test_limit_query_type(self):
        """Test LimitQuery type definition"""
        origin = typing.get_origin(LimitQuery)
        args = typing.get_args(LimitQuery)

        assert origin is typing.Annotated
        assert args[0] is int
        assert isinstance(args[1], Query)

    def test_offset_query_type(self):
        """Test OffsetQuery type definition"""
        origin = typing.get_origin(OffsetQuery)
        args = typing.get_args(OffsetQuery)

        assert origin is typing.Annotated
        assert args[0] is int
        assert isinstance(args[1], Query)


class TestFieldInfoIntegration:
    """Test integration with Pydantic FieldInfo"""

    def test_param_is_field_info(self):
        """Test Param is instance of FieldInfo"""
        param = Param()
        assert isinstance(param, FieldInfo)

    def test_body_is_field_info(self):
        """Test Body is instance of FieldInfo"""
        body = Body()
        assert isinstance(body, FieldInfo)

    def test_param_stores_custom_attributes(self):
        """Test Param stores custom attributes correctly"""
        param = Param(
            default="test", examples=["example1", "example2"], include_in_schema=False
        )

        assert param.default == "test"
        assert param.examples == ["example1", "example2"]
        assert param.include_in_schema is False

    def test_body_stores_custom_attributes(self):
        """Test Body stores custom attributes correctly"""
        body = Body(
            embed=True, media_type="application/xml", examples=[{"test": "data"}]
        )

        assert body.embed is True
        assert body.media_type == "application/xml"
        assert body.examples == [{"test": "data"}]
