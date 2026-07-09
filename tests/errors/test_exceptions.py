from http import HTTPStatus

import pytest

from fastopenapi.errors import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    BadRequestError,
    CircularDependencyError,
    DependencyError,
    ErrorType,
    InternalServerError,
    ResourceConflictError,
    ResourceNotFoundError,
    SecurityError,
    ServiceUnavailableError,
    ValidationError,
)

EXPECTED = [
    (BadRequestError, HTTPStatus.BAD_REQUEST, ErrorType.BAD_REQUEST),
    (ValidationError, HTTPStatus.UNPROCESSABLE_ENTITY, ErrorType.VALIDATION_ERROR),
    (ResourceNotFoundError, HTTPStatus.NOT_FOUND, ErrorType.RESOURCE_NOT_FOUND),
    (AuthenticationError, HTTPStatus.UNAUTHORIZED, ErrorType.AUTHENTICATION_ERROR),
    (AuthorizationError, HTTPStatus.FORBIDDEN, ErrorType.AUTHORIZATION_ERROR),
    (ResourceConflictError, HTTPStatus.CONFLICT, ErrorType.RESOURCE_CONFLICT),
    (
        InternalServerError,
        HTTPStatus.INTERNAL_SERVER_ERROR,
        ErrorType.INTERNAL_SERVER_ERROR,
    ),
    (
        ServiceUnavailableError,
        HTTPStatus.SERVICE_UNAVAILABLE,
        ErrorType.INTERNAL_SERVER_ERROR,
    ),
    (
        DependencyError,
        HTTPStatus.INTERNAL_SERVER_ERROR,
        ErrorType.INTERNAL_SERVER_ERROR,
    ),
    (
        CircularDependencyError,
        HTTPStatus.INTERNAL_SERVER_ERROR,
        ErrorType.INTERNAL_SERVER_ERROR,
    ),
    (SecurityError, HTTPStatus.FORBIDDEN, ErrorType.AUTHORIZATION_ERROR),
]


class TestErrorClasses:
    @pytest.mark.parametrize("cls,status,_", EXPECTED)
    def test_status_codes(self, cls, status, _):
        assert cls().status_code == status

    def test_service_unavailable_error_type(self):
        assert ServiceUnavailableError().error_type == ErrorType.SERVICE_UNAVAILABLE

    def test_security_error_type(self):
        assert SecurityError().error_type == ErrorType.AUTHORIZATION_ERROR

    def test_default_message_used_when_none(self):
        err = BadRequestError()
        assert err.message == "Bad request"
        assert str(err) == "Bad request"

    def test_custom_message_and_details(self):
        err = ValidationError("Bad field", details="field 'x' must be int")
        assert err.message == "Bad field"
        assert err.details == "field 'x' must be int"


class TestToResponse:
    def test_structure_without_details(self):
        body = ResourceNotFoundError("Nope").to_response()
        assert body == {
            "error": {
                "type": ErrorType.RESOURCE_NOT_FOUND,
                "message": "Nope",
                "status": HTTPStatus.NOT_FOUND,
            }
        }

    def test_details_included_when_set(self):
        body = ValidationError("Bad", details="why").to_response()
        assert body["error"]["details"] == "why"

    def test_error_type_and_status_are_json_friendly(self):
        body = BadRequestError().to_response()
        assert isinstance(body["error"]["type"], str)
        assert isinstance(body["error"]["status"], int)


class TestFromException:
    def test_api_error_returned_as_is(self):
        err = AuthenticationError("no token")
        assert APIError.from_exception(err) is err

    def test_mapper_converts_known_exception(self):
        result = APIError.from_exception(
            KeyError("user"), {KeyError: ResourceNotFoundError}
        )
        assert isinstance(result, ResourceNotFoundError)
        assert result.status_code == HTTPStatus.NOT_FOUND

    def test_status_code_attribute_used(self):
        class Custom(Exception):
            status_code = 404

        result = APIError.from_exception(Custom("gone"))
        assert result.status_code == HTTPStatus.NOT_FOUND
        assert result.error_type == ErrorType.RESOURCE_NOT_FOUND

    def test_code_attribute_used(self):
        class Custom(Exception):
            code = 409

        result = APIError.from_exception(Custom("conflict"))
        assert result.status_code == HTTPStatus.CONFLICT
        assert result.error_type == ErrorType.RESOURCE_CONFLICT

    def test_non_numeric_code_falls_back_to_500(self):
        class Custom(Exception):
            code = "not-a-status"

        result = APIError.from_exception(Custom("boom"))
        assert result.status_code == HTTPStatus.INTERNAL_SERVER_ERROR

    def test_message_attribute_preferred_over_str(self):
        class Custom(Exception):
            status_code = 400

            def __init__(self):
                super().__init__("raw str")
                self.message = "from attribute"

        result = APIError.from_exception(Custom())
        assert result.message == "from attribute"

    def test_plain_exception_maps_to_500(self):
        result = APIError.from_exception(RuntimeError("boom"))
        assert result.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert result.error_type == ErrorType.INTERNAL_SERVER_ERROR

    def test_5xx_message_is_generic(self):
        result = APIError.from_exception(RuntimeError("db password is hunter2"))
        assert result.message == "Internal server error"
        assert result.details is None

    def test_5xx_details_included_with_debug(self):
        result = APIError.from_exception(RuntimeError("boom"), debug=True)
        assert result.message == "Internal server error"
        assert result.details == "RuntimeError: boom"

    def test_derived_5xx_uses_status_phrase(self):
        class Custom(Exception):
            status_code = 503

        result = APIError.from_exception(Custom("backend down"))
        assert result.status_code == HTTPStatus.SERVICE_UNAVAILABLE
        assert result.message == "Service Unavailable"
        assert "backend down" not in result.message

    def test_attribute_error_name_not_used_as_message(self):
        # AttributeError carries a 'name' attribute (py3.10+); it must not
        # surface as the client-facing message
        exc = AttributeError(
            "'coroutine' object has no attribute 'get'", name="get", obj=None
        )
        result = APIError.from_exception(exc)
        assert result.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert result.message == "Internal server error"

    def test_non_http_int_code_falls_back_to_500(self):
        class Custom(Exception):
            code = 42  # errno-style code, not an HTTP status

        result = APIError.from_exception(Custom("boom"))
        assert result.status_code == HTTPStatus.INTERNAL_SERVER_ERROR

    def test_4xx_message_heuristic_requires_string(self):
        class Custom(Exception):
            status_code = 404

            def __init__(self):
                super().__init__("not found via str")
                self.message = 12345  # non-string attribute is skipped

        result = APIError.from_exception(Custom())
        assert result.status_code == HTTPStatus.NOT_FOUND
        assert result.message == "not found via str"
