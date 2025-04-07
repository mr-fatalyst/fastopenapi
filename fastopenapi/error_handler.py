from enum import Enum
from http import HTTPStatus
from typing import Any


class ErrorType(str, Enum):
    """Enum defining standard error types for RESTful API responses."""

    VALIDATION_ERROR = "validation_error"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    RESOURCE_NOT_FOUND = "resource_not_found"
    RESOURCE_CONFLICT = "resource_conflict"
    INTERNAL_SERVER_ERROR = "internal_server_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    BAD_REQUEST = "bad_request"


class APIError(Exception):
    """
    Base exception class for all API errors.
    Provides standardized error response formatting.
    """

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
        """Convert to standardized error response."""
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


class BadRequestError(APIError):
    """Exception for bad requests."""

    status_code = HTTPStatus.BAD_REQUEST
    default_message = "Bad request"
    error_type = ErrorType.BAD_REQUEST


class ValidationError(APIError):
    """Exception for validation errors."""

    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    default_message = "Validation error"
    error_type = ErrorType.VALIDATION_ERROR


class ResourceNotFoundError(APIError):
    """Exception for resource not found errors."""

    status_code = HTTPStatus.NOT_FOUND
    default_message = "Resource not found"
    error_type = ErrorType.RESOURCE_NOT_FOUND


class AuthenticationError(APIError):
    """Exception for authentication errors."""

    status_code = HTTPStatus.UNAUTHORIZED
    default_message = "Authentication required"
    error_type = ErrorType.AUTHENTICATION_ERROR


class AuthorizationError(APIError):
    """Exception for authorization errors."""

    status_code = HTTPStatus.FORBIDDEN
    default_message = "Permission denied"
    error_type = ErrorType.AUTHORIZATION_ERROR


class ResourceConflictError(APIError):
    """Exception for resource conflict errors."""

    status_code = HTTPStatus.CONFLICT
    default_message = "Resource conflict"
    error_type = ErrorType.RESOURCE_CONFLICT


class InternalServerError(APIError):
    """Exception for internal server errors."""

    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    default_message = "Internal server error"
    error_type = ErrorType.INTERNAL_SERVER_ERROR


class ServiceUnavailableError(APIError):
    """Exception for service unavailable errors."""

    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    default_message = "Service unavailable"
    error_type = ErrorType.SERVICE_UNAVAILABLE


def format_exception_response(exception: Exception) -> dict[str, Any]:
    """
    Convert any exception to a standardized error response.
    Uses the exception's to_response method if available.
    """
    if isinstance(exception, APIError):
        return exception.to_response()

    # Handle framework-specific exceptions
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR

    # Try to extract status code
    if hasattr(exception, "status_code"):
        status_code = exception.status_code
    elif hasattr(exception, "code"):
        status_code = exception.code

    # Try to extract error message
    if hasattr(exception, "message"):
        message = exception.message
    elif hasattr(exception, "title"):
        message = exception.title
    elif hasattr(exception, "name"):
        message = exception.name
    elif hasattr(exception, "reason"):
        message = exception.reason
    elif hasattr(exception, "detail"):
        message = exception.detail
    else:
        message = str(exception)

    # Create generic APIError with extracted information
    error_type = APIError.STATUS_TO_ERROR_TYPE.get(
        HTTPStatus(status_code), ErrorType.INTERNAL_SERVER_ERROR
    )

    generic_error = APIError(message=message)
    generic_error.status_code = status_code
    generic_error.error_type = error_type

    return generic_error.to_response()
