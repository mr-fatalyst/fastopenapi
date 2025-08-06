from http import HTTPStatus
from typing import Any

from fastopenapi.errors.types import ErrorType


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
