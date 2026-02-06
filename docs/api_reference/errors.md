# Errors API Reference

Complete reference for error handling classes in FastOpenAPI.

## Error Class Hierarchy

```
APIError (base)
├── BadRequestError
├── ValidationError
├── ResourceNotFoundError
├── AuthenticationError
├── AuthorizationError
├── ResourceConflictError
├── InternalServerError
│   └── DependencyError
│       ├── CircularDependencyError
│       └── SecurityError
└── ServiceUnavailableError
```

---

## APIError

Base exception class for all API errors.

```python
from fastopenapi.errors import APIError
```

### Class Definition

```python
class APIError(Exception):
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    default_message = "An error occurred"
    error_type = ErrorType.INTERNAL_SERVER_ERROR

    def __init__(
        self,
        message: str | None = None,
        details: Any | None = None,
    )
```

### Attributes

- **status_code** (`HTTPStatus`): HTTP status code (default: `500`)
- **default_message** (`str`): Default error message
- **error_type** (`ErrorType`): Error type identifier
- **message** (`str`): Error message
- **details** (`Any`): Additional error details

### Methods

#### to_response()

Convert to standardized error response.

```python
def to_response() -> dict[str, Any]
```

**Returns**: Standardized error dictionary

**Example**:
```python
error = BadRequestError("Invalid input")
response = error.to_response()
# {
#     "error": {
#         "type": "bad_request",
#         "message": "Invalid input",
#         "status": 400
#     }
# }
```

#### from_exception()

Convert any exception to an APIError.

```python
@classmethod
def from_exception(
    exc: Exception,
    mapper: dict[type[Exception], type[APIError]] | None = None,
) -> APIError
```

**Parameters**:
- `exc`: Exception to convert
- `mapper`: Optional mapping of exception types to APIError subclasses

**Returns**: APIError instance

**Example**:
```python
try:
    # Some code that may raise ValueError
    raise ValueError("Invalid value")
except Exception as e:
    api_error = APIError.from_exception(e)
    # Returns APIError with message "Invalid value" and status 500
```

---

## BadRequestError

HTTP 400 - Bad Request

```python
from fastopenapi.errors import BadRequestError
```

### Definition

```python
class BadRequestError(APIError):
    status_code = HTTPStatus.BAD_REQUEST  # 400
    default_message = "Bad request"
    error_type = ErrorType.BAD_REQUEST
```

### Usage

```python
@router.post("/items")
def create_item(name: str = Body(...)):
    if not name.strip():
        raise BadRequestError("Item name cannot be empty")

    return {"name": name}
```

### Response Format

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": {
    "type": "bad_request",
    "message": "Item name cannot be empty",
    "status": 400
  }
}
```

---

## ValidationError

HTTP 422 - Unprocessable Entity

```python
from fastopenapi.errors import ValidationError
```

### Definition

```python
class ValidationError(APIError):
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY  # 422
    default_message = "Validation error"
    error_type = ErrorType.VALIDATION_ERROR
```

### Usage

```python
@router.post("/items")
def create_item(price: float):
    if price < 0:
        raise ValidationError(
            message="Price must be positive",
            details={"field": "price", "value": price}
        )

    return {"price": price}
```

### Response Format

```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json

{
  "error": {
    "type": "validation_error",
    "message": "Validation error",
    "status": 422,
    "details": [
      {
        "loc": ["body", "email"],
        "msg": "value is not a valid email address",
        "type": "value_error.email"
      }
    ]
  }
}
```

---

## ResourceNotFoundError

HTTP 404 - Not Found

```python
from fastopenapi.errors import ResourceNotFoundError
```

### Definition

```python
class ResourceNotFoundError(APIError):
    status_code = HTTPStatus.NOT_FOUND  # 404
    default_message = "Resource not found"
    error_type = ErrorType.RESOURCE_NOT_FOUND
```

### Usage

```python
@router.get("/users/{user_id}")
def get_user(user_id: int):
    user = database.get_user(user_id)
    if not user:
        raise ResourceNotFoundError(f"User {user_id} not found")

    return user
```

### Response Format

```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "error": {
    "type": "resource_not_found",
    "message": "User 123 not found",
    "status": 404
  }
}
```

---

## AuthenticationError

HTTP 401 - Unauthorized

```python
from fastopenapi.errors import AuthenticationError
```

### Definition

```python
class AuthenticationError(APIError):
    status_code = HTTPStatus.UNAUTHORIZED  # 401
    default_message = "Authentication required"
    error_type = ErrorType.AUTHENTICATION_ERROR
```

### Usage

```python
def get_current_user(token: str = Header(..., alias="Authorization")):
    if not token.startswith("Bearer "):
        raise AuthenticationError("Invalid token format")

    user = verify_token(token[7:])
    if not user:
        raise AuthenticationError("Invalid or expired token")

    return user

@router.get("/profile")
def get_profile(user = Depends(get_current_user)):
    return user
```

### Response Format

```http
HTTP/1.1 401 Unauthorized
Content-Type: application/json

{
  "error": {
    "type": "authentication_error",
    "message": "Invalid or expired token",
    "status": 401
  }
}
```

---

## AuthorizationError

HTTP 403 - Forbidden

```python
from fastopenapi.errors import AuthorizationError
```

### Definition

```python
class AuthorizationError(APIError):
    status_code = HTTPStatus.FORBIDDEN  # 403
    default_message = "Permission denied"
    error_type = ErrorType.AUTHORIZATION_ERROR
```

### Usage

```python
def require_admin(current_user = Depends(get_current_user)):
    if not current_user.is_admin:
        raise AuthorizationError("Admin access required")

    return current_user

@router.delete("/users/{user_id}")
def delete_user(user_id: int, admin = Depends(require_admin)):
    database.delete_user(user_id)
    return {"deleted": user_id}
```

### Response Format

```http
HTTP/1.1 403 Forbidden
Content-Type: application/json

{
  "error": {
    "type": "authorization_error",
    "message": "Admin access required",
    "status": 403
  }
}
```

---

## ResourceConflictError

HTTP 409 - Conflict

```python
from fastopenapi.errors import ResourceConflictError
```

### Definition

```python
class ResourceConflictError(APIError):
    status_code = HTTPStatus.CONFLICT  # 409
    default_message = "Resource conflict"
    error_type = ErrorType.RESOURCE_CONFLICT
```

### Usage

```python
@router.post("/users")
def create_user(username: str, email: str):
    if database.user_exists(username):
        raise ResourceConflictError(
            f"Username '{username}' already exists"
        )

    if database.email_exists(email):
        raise ResourceConflictError(
            f"Email '{email}' already registered"
        )

    user = database.create_user(username, email)
    return user
```

### Response Format

```http
HTTP/1.1 409 Conflict
Content-Type: application/json

{
  "error": {
    "type": "resource_conflict",
    "message": "Username 'john' already exists",
    "status": 409
  }
}
```

---

## InternalServerError

HTTP 500 - Internal Server Error

```python
from fastopenapi.errors import InternalServerError
```

### Definition

```python
class InternalServerError(APIError):
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR  # 500
    default_message = "Internal server error"
    error_type = ErrorType.INTERNAL_SERVER_ERROR
```

### Usage

```python
@router.get("/items")
def list_items():
    try:
        items = database.get_all_items()
        return items
    except DatabaseError as e:
        raise InternalServerError(
            message="Database error occurred",
            details=str(e)
        )
```

### Response Format

```http
HTTP/1.1 500 Internal Server Error
Content-Type: application/json

{
  "error": {
    "type": "internal_server_error",
    "message": "Database error occurred",
    "status": 500,
    "details": "Connection timeout"
  }
}
```

---

## ServiceUnavailableError

HTTP 503 - Service Unavailable

```python
from fastopenapi.errors import ServiceUnavailableError
```

### Definition

```python
class ServiceUnavailableError(APIError):
    status_code = HTTPStatus.SERVICE_UNAVAILABLE  # 503
    default_message = "Service unavailable"
    error_type = ErrorType.SERVICE_UNAVAILABLE
```

### Usage

```python
@router.get("/items")
def list_items():
    if not database.is_connected():
        raise ServiceUnavailableError("Database is unavailable")

    return database.get_all_items()
```

---

## Dependency Errors

### DependencyError

Base exception for dependency resolution errors.

```python
from fastopenapi.errors import DependencyError
```

```python
class DependencyError(InternalServerError):
    default_message = "dependency_error"
```

### CircularDependencyError

Raised when circular dependencies are detected.

```python
from fastopenapi.errors import CircularDependencyError
```

```python
class CircularDependencyError(DependencyError):
    default_message = "circular_dependency_error"
```

### SecurityError

Raised when security requirements are not met.

```python
from fastopenapi.errors import SecurityError
```

```python
class SecurityError(DependencyError):
    status_code = HTTPStatus.FORBIDDEN  # 403
    default_message = "insufficient_scope"
    error_type = ErrorType.AUTHORIZATION_ERROR
```

---

## Exception Mapping

Map framework-specific exceptions to API errors:

```python
from fastopenapi.routers.base import BaseAdapter

# Custom exception mapper
EXCEPTION_MAPPER = {
    ValueError: BadRequestError,
    KeyError: ResourceNotFoundError,
    PermissionError: AuthorizationError,
}

class MyRouter(BaseAdapter):
    EXCEPTION_MAPPER = EXCEPTION_MAPPER
```

### STATUS_TO_ERROR_TYPE

A mapping of HTTP status codes to error types, used internally for exception conversion:

```python
from fastopenapi.errors.exceptions import STATUS_TO_ERROR_TYPE

# STATUS_TO_ERROR_TYPE = {
#     HTTPStatus.BAD_REQUEST: ErrorType.BAD_REQUEST,
#     HTTPStatus.UNAUTHORIZED: ErrorType.AUTHENTICATION_ERROR,
#     HTTPStatus.FORBIDDEN: ErrorType.AUTHORIZATION_ERROR,
#     HTTPStatus.NOT_FOUND: ErrorType.RESOURCE_NOT_FOUND,
#     HTTPStatus.CONFLICT: ErrorType.RESOURCE_CONFLICT,
#     HTTPStatus.UNPROCESSABLE_ENTITY: ErrorType.VALIDATION_ERROR,
#     HTTPStatus.INTERNAL_SERVER_ERROR: ErrorType.INTERNAL_SERVER_ERROR,
#     HTTPStatus.SERVICE_UNAVAILABLE: ErrorType.SERVICE_UNAVAILABLE,
# }
```

This is used by `APIError.from_exception()` to determine the error type when converting framework exceptions.

---

## Custom Errors

Create custom error classes:

```python
from fastopenapi.errors import APIError
from http import HTTPStatus

class RateLimitError(APIError):
    status_code = HTTPStatus.TOO_MANY_REQUESTS  # 429
    default_message = "Rate limit exceeded"
    error_type = "rate_limit_error"

@router.get("/api/data")
def get_data():
    if rate_limiter.is_exceeded():
        raise RateLimitError("Too many requests. Try again later.")

    return {"data": "..."}
```

---

## Error Response Structure

All errors follow this structure:

```json
{
  "error": {
    "type": "error_type_identifier",
    "message": "Human-readable error message",
    "status": 400,
    "details": {
      // Optional additional details
    }
  }
}
```

---

## Best Practices

### 1. Use Specific Error Classes

```python
# Good
raise ResourceNotFoundError(f"User {user_id} not found")

# Avoid
raise Exception("User not found")
```

### 2. Provide Helpful Messages

```python
# Good
raise BadRequestError("Email format is invalid. Expected: user@example.com")

# Avoid
raise BadRequestError("Invalid input")
```

### 3. Include Details for Validation Errors

```python
raise ValidationError(
    message="Validation failed",
    details=[
        {"field": "email", "error": "Invalid format"},
        {"field": "age", "error": "Must be >= 18"}
    ]
)
```

### 4. Don't Expose Sensitive Information

```python
# Good
raise InternalServerError("Database error occurred")

# Avoid
raise InternalServerError(f"SQL error: {sql_exception.query}")
```

---

## See Also

- [Error Handling Guide](../guide/error_handling.md) - Error handling patterns
- [Security Guide](../guide/security.md) - Authentication and authorization
- [Dependencies Reference](dependencies.md) - Dependency injection
