from http import HTTPStatus
from typing import Any

from fastopenapi.errors.types import ErrorType

# Mapping common HTTP status codes to ErrorTypes
STATUS_TO_ERROR_TYPE = {
    HTTPStatus.BAD_REQUEST: ErrorType.BAD_REQUEST,
    HTTPStatus.UNAUTHORIZED: ErrorType.AUTHENTICATION_ERROR,
    HTTPStatus.FORBIDDEN: ErrorType.AUTHORIZATION_ERROR,
    HTTPStatus.NOT_FOUND: ErrorType.RESOURCE_NOT_FOUND,
    HTTPStatus.CONFLICT: ErrorType.RESOURCE_CONFLICT,
    HTTPStatus.UNPROCESSABLE_ENTITY: ErrorType.VALIDATION_ERROR,
    HTTPStatus.INTERNAL_SERVER_ERROR: ErrorType.INTERNAL_SERVER_ERROR,
    HTTPStatus.SERVICE_UNAVAILABLE: ErrorType.SERVICE_UNAVAILABLE,
}


class APIError(Exception):
    """Base exception class for all API errors"""

    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    default_message = "An error occurred"
    error_type = ErrorType.INTERNAL_SERVER_ERROR

    def __init__(
        self,
        message: str | None = None,
        details: Any | None = None,
    ):
        self.message = message or self.default_message
        self.details = details
        super().__init__(self.message)

    def to_response(self) -> dict[str, Any]:
        """Convert to standardized error response"""
        error_dict = {
            "error": {
                "type": self.error_type,
                "message": self.message,
                "status": self.status_code,
            }
        }
        if self.details:
            error_dict["error"]["details"] = self.details
        return error_dict

    @classmethod
    def from_exception(
        cls,
        exc: Exception,
        mapper: dict[type[Exception], type["APIError"]] | None = None,
    ) -> "APIError":
        """Convert any exception to a standardized error response"""
        if isinstance(exc, APIError):
            return exc

        mapper = mapper or {}
        entry = mapper.get(type(exc))
        if entry:
            return entry(str(exc))

        status = HTTPStatus.INTERNAL_SERVER_ERROR
        for attr in ("status_code", "code"):
            if hasattr(exc, attr):
                try:
                    status = HTTPStatus(int(getattr(exc, attr)))
                    break
                except Exception:
                    pass

        message = str(exc)
        for attr in ("message", "title", "name", "reason", "detail"):
            if hasattr(exc, attr):
                message = str(getattr(exc, attr))
                break

        err_type = STATUS_TO_ERROR_TYPE.get(status, ErrorType.INTERNAL_SERVER_ERROR)

        api_error = APIError(message=message)
        api_error.status_code = status
        api_error.error_type = err_type
        return api_error


class BadRequestError(APIError):
    status_code = HTTPStatus.BAD_REQUEST
    default_message = "Bad request"
    error_type = ErrorType.BAD_REQUEST


class ValidationError(APIError):
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    default_message = "Validation error"
    error_type = ErrorType.VALIDATION_ERROR


class ResourceNotFoundError(APIError):
    status_code = HTTPStatus.NOT_FOUND
    default_message = "Resource not found"
    error_type = ErrorType.RESOURCE_NOT_FOUND


class AuthenticationError(APIError):
    status_code = HTTPStatus.UNAUTHORIZED
    default_message = "Authentication required"
    error_type = ErrorType.AUTHENTICATION_ERROR


class AuthorizationError(APIError):
    status_code = HTTPStatus.FORBIDDEN
    default_message = "Permission denied"
    error_type = ErrorType.AUTHORIZATION_ERROR


class ResourceConflictError(APIError):
    status_code = HTTPStatus.CONFLICT
    default_message = "Resource conflict"
    error_type = ErrorType.RESOURCE_CONFLICT


class InternalServerError(APIError):
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    default_message = "Internal server error"
    error_type = ErrorType.INTERNAL_SERVER_ERROR


class ServiceUnavailableError(APIError):
    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    default_message = "Service unavailable"
    error_type = ErrorType.SERVICE_UNAVAILABLE
