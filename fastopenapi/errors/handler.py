from http import HTTPStatus
from typing import Any

from fastopenapi.errors.exceptions import APIError
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


def format_exception_response(exception: Exception) -> dict[str, Any]:
    """Convert any exception to a standardized error response"""
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
    message = str(exception)
    for attr in ["message", "title", "name", "reason", "detail"]:
        if hasattr(exception, attr):
            message = getattr(exception, attr)
            break

    # Create generic APIError with extracted information
    error_type = STATUS_TO_ERROR_TYPE.get(
        HTTPStatus(status_code), ErrorType.INTERNAL_SERVER_ERROR
    )

    generic_error = APIError(message=message)
    generic_error.status_code = status_code
    generic_error.error_type = error_type

    return generic_error.to_response()
