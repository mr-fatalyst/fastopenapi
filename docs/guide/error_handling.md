# Error Handling

This guide covers how to handle errors and exceptions in FastOpenAPI.

## Built-in Exceptions

FastOpenAPI provides standard exception classes for common HTTP errors.

### Importing Exceptions

```python
from fastopenapi.errors import (
    BadRequestError,
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError,
    ResourceConflictError,
    ValidationError,
    InternalServerError,
    ServiceUnavailableError
)
```

### Exception Classes

| Exception | Status Code | Use Case |
|-----------|-------------|----------|
| `BadRequestError` | 400 | Invalid request format |
| `AuthenticationError` | 401 | Authentication required or failed |
| `AuthorizationError` | 403 | User lacks permission |
| `ResourceNotFoundError` | 404 | Resource doesn't exist |
| `ResourceConflictError` | 409 | Resource conflict (duplicate, etc.) |
| `ValidationError` | 422 | Request validation failed |
| `InternalServerError` | 500 | Server error |
| `ServiceUnavailableError` | 503 | Service temporarily unavailable |

## Basic Error Handling

### Raising Exceptions

```python
from fastopenapi.errors import ResourceNotFoundError

@router.get("/users/{user_id}")
def get_user(user_id: int):
    user = database.get_user(user_id)
    if not user:
        raise ResourceNotFoundError(f"User {user_id} not found")
    return user
```

### With Custom Message

```python
from fastopenapi.errors import BadRequestError

@router.post("/items")
def create_item(item: Item):
    if item.price < 0:
        raise BadRequestError("Price cannot be negative")
    return {"item": item}
```

### With Details

```python
from fastopenapi.errors import ValidationError

@router.post("/users")
def create_user(user: UserCreate):
    existing = database.get_user_by_email(user.email)
    if existing:
        raise ValidationError(
            message="User already exists",
            details={"email": user.email, "user_id": existing.id}
        )
    return database.create_user(user)
```

## Error Response Format

All errors return a standardized JSON format:

```json
{
  "error": {
    "type": "resource_not_found",
    "message": "User 123 not found",
    "status": 404
  }
}
```

**Note:** The `details` field is only included when it has a truthy value. When no details are provided, the field is omitted entirely.

### With Details

```json
{
  "error": {
    "type": "validation_error",
    "message": "Error parsing parameter 'email'",
    "status": 422,
    "details": "Value is not a valid email address"
  }
}
```

## Validation Errors

Pydantic validation errors are automatically caught:

### Request Validation

```python
class User(BaseModel):
    name: str
    age: int = Field(..., ge=0, le=120)
    email: EmailStr

@router.post("/users")
def create_user(user: User):
    return user
```

**Invalid Request:**
```http
POST /users
Content-Type: application/json

{"name": "John", "age": -5, "email": "invalid"}
```

**Error Response:**
```json
{
  "error": {
    "type": "validation_error",
    "message": "Validation error for parameter 'age'",
    "status": 422,
    "details": "Input should be greater than or equal to 0 ..."
  }
}
```

> **Note:** The `details` field is a string representation of the Pydantic validation error message. If there are no details, the field is omitted entirely.

## Common Error Patterns

### Not Found Pattern

```python
@router.get("/items/{item_id}")
def get_item(item_id: int):
    item = database.get(item_id)
    if not item:
        raise ResourceNotFoundError(f"Item {item_id} not found")
    return item
```

### Authorization Pattern

```python
@router.delete("/items/{item_id}")
def delete_item(
    item_id: int,
    current_user: User = Depends(get_current_user)
):
    item = database.get(item_id)
    if not item:
        raise ResourceNotFoundError(f"Item {item_id} not found")
    
    if item.owner_id != current_user.id:
        raise AuthorizationError("You don't own this item")
    
    database.delete(item_id)
    return {"deleted": True}
```

### Conflict Pattern

```python
@router.post("/users")
def create_user(user: UserCreate):
    existing = database.get_user_by_email(user.email)
    if existing:
        raise ResourceConflictError(f"User with email {user.email} already exists")
    
    return database.create_user(user)
```

### Bad Request Pattern

```python
@router.post("/orders")
def create_order(order: OrderCreate):
    if not order.items:
        raise BadRequestError("Order must contain at least one item")
    
    total = sum(item.price * item.quantity for item in order.items)
    if total <= 0:
        raise BadRequestError("Order total must be positive")
    
    return database.create_order(order)
```

## Framework-Specific Exceptions

You can also use framework-specific exceptions:

### Flask

```python
from flask import abort

@router.get("/users/{user_id}")
def get_user(user_id: int):
    user = database.get(user_id)
    if not user:
        abort(404, description="User not found")
    return user
```

### Django

```python
from django.http import Http404

@router.get("/users/{user_id}")
def get_user(user_id: int):
    user = database.get(user_id)
    if not user:
        raise Http404("User not found")
    return user
```

### Starlette

```python
from starlette.exceptions import HTTPException

@router.get("/users/{user_id}")
async def get_user(user_id: int):
    user = await database.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

### Falcon

```python
import falcon

@router.get("/users/{user_id}")
async def get_user(user_id: int):
    user = await database.get(user_id)
    if not user:
        raise falcon.HTTPNotFound(description="User not found")
    return user
```

## Try-Except Blocks

### Catching Specific Errors

```python
@router.post("/items")
def create_item(item: Item):
    try:
        result = database.create(item)
        return result
    except DatabaseConnectionError:
        raise ServiceUnavailableError("Database temporarily unavailable")
    except DuplicateKeyError as e:
        raise ResourceConflictError(f"Item already exists: {e}")
```

### Generic Error Handling

```python
import logging

logger = logging.getLogger(__name__)

@router.post("/process")
def process_data(data: dict):
    try:
        result = complex_processing(data)
        return result
    except ValueError as e:
        raise BadRequestError(f"Invalid data: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise InternalServerError("An unexpected error occurred")
```

## Custom Error Responses

### Creating Custom Exceptions

```python
from fastopenapi.errors import APIError
from http import HTTPStatus

class PaymentRequiredError(APIError):
    status_code = HTTPStatus.PAYMENT_REQUIRED
    default_message = "Payment required"
    error_type = "payment_required"

@router.get("/premium-content")
def get_premium_content(current_user: User = Depends(get_current_user)):
    if not current_user.is_premium:
        raise PaymentRequiredError("Premium subscription required")
    return {"content": "premium data"}
```

### Custom Error Details

```python
class InsufficientBalanceError(APIError):
    status_code = HTTPStatus.PAYMENT_REQUIRED
    default_message = "Insufficient balance"
    error_type = "insufficient_balance"

@router.post("/purchases")
def create_purchase(purchase: Purchase, user: User = Depends(get_current_user)):
    if user.balance < purchase.amount:
        raise InsufficientBalanceError(
            message=f"Insufficient balance. Required: {purchase.amount}, Available: {user.balance}",
            details={
                "required": purchase.amount,
                "available": user.balance,
                "shortfall": purchase.amount - user.balance
            }
        )
    
    return process_purchase(purchase, user)
```

## Error Logging

### Basic Logging

```python
import logging

logger = logging.getLogger(__name__)

@router.post("/items")
def create_item(item: Item):
    try:
        result = database.create(item)
        return result
    except Exception as e:
        logger.error(f"Failed to create item: {str(e)}", exc_info=True)
        raise InternalServerError("Failed to create item")
```

### Structured Logging

```python
import structlog

logger = structlog.get_logger()

@router.get("/users/{user_id}")
def get_user(user_id: int):
    try:
        user = database.get(user_id)
        if not user:
            logger.warning("user_not_found", user_id=user_id)
            raise ResourceNotFoundError(f"User {user_id} not found")
        return user
    except Exception as e:
        logger.error(
            "user_fetch_failed",
            user_id=user_id,
            error=str(e),
            exc_info=True
        )
        raise
```

## Error Context

### Adding Request Context

```python
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar('request_id', default=None)

def get_request_id():
    return request_id_var.get() or "unknown"

@router.get("/items/{item_id}")
def get_item(
    item_id: int,
    request_id: str = Header(..., alias="X-Request-ID")
):
    request_id_var.set(request_id)
    
    try:
        item = database.get(item_id)
        if not item:
            raise ResourceNotFoundError(f"Item {item_id} not found")
        return item
    except Exception as e:
        logger.error(
            f"Error processing request {get_request_id()}: {str(e)}",
            exc_info=True
        )
        raise
```

## Validation Error Customization

### Custom Field Validators

```python
from pydantic import field_validator

class User(BaseModel):
    username: str
    age: int
    
    @field_validator('username')
    @classmethod
    def username_valid(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        if not v.isalnum():
            raise ValueError("Username must be alphanumeric")
        return v
    
    @field_validator('age')
    @classmethod
    def age_valid(cls, v: int) -> int:
        if v < 13:
            raise ValueError("Must be at least 13 years old")
        return v
```

**Error Response:**
```json
{
  "error": {
    "type": "validation_error",
    "message": "Validation error",
    "status": 422,
    "details": [
      {
        "loc": ["body", "username"],
        "msg": "Username must be alphanumeric",
        "type": "value_error"
      }
    ]
  }
}
```

## Error Recovery

### Fallback Values

```python
@router.get("/config")
def get_config():
    try:
        config = load_config_from_database()
        return config
    except DatabaseError:
        logger.warning("Failed to load config from database, using defaults")
        return get_default_config()
```

### Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_fixed

@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
def fetch_external_data(url: str):
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    return response.json()

@router.get("/external-data")
def get_external_data():
    try:
        data = fetch_external_data("https://api.example.com/data")
        return data
    except Exception as e:
        logger.error(f"Failed to fetch external data: {str(e)}")
        raise ServiceUnavailableError("External service unavailable")
```

## Partial Failure Handling

### Batch Operations

```python
class BatchResult(BaseModel):
    succeeded: list[int]
    failed: list[dict]

@router.post("/items/batch", response_model=BatchResult)
def create_items_batch(items: list[Item]):
    succeeded = []
    failed = []
    
    for idx, item in enumerate(items):
        try:
            result = database.create(item)
            succeeded.append(result.id)
        except Exception as e:
            failed.append({
                "index": idx,
                "item": item.model_dump(),
                "error": str(e)
            })
    
    return BatchResult(succeeded=succeeded, failed=failed)
```

## Error Monitoring

### Sentry Integration

```python
import sentry_sdk

sentry_sdk.init(dsn="your-sentry-dsn")

@router.post("/critical-operation")
def critical_operation(data: dict):
    try:
        result = perform_critical_task(data)
        return result
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.error(f"Critical operation failed: {str(e)}", exc_info=True)
        raise InternalServerError("Operation failed")
```

## Debugging Errors

### Development Mode

```python
import os

DEBUG = os.getenv("DEBUG", "false").lower() == "true"

@router.post("/items")
def create_item(item: Item):
    try:
        result = database.create(item)
        return result
    except Exception as e:
        if DEBUG:
            # Return full traceback in development
            import traceback
            raise InternalServerError(
                message="Operation failed",
                details={
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
            )
        else:
            # Hide details in production
            logger.error(f"Failed to create item: {str(e)}", exc_info=True)
            raise InternalServerError("Failed to create item")
```

## Best Practices

### 1. Use Appropriate Status Codes

```python
# Good - specific error
raise ResourceNotFoundError("User not found")  # 404

# Avoid - generic error
raise InternalServerError("User not found")  # 500
```

### 2. Provide Helpful Messages

```python
# Good - actionable message
raise BadRequestError("Email is required. Please provide a valid email address")

# Avoid - vague message
raise BadRequestError("Invalid input")
```

### 3. Don't Expose Sensitive Information

```python
# Good
raise AuthenticationError("Invalid credentials")

# Avoid - reveals which field is wrong
raise AuthenticationError("Password is incorrect")
```

### 4. Log Before Raising

```python
# Good
try:
    database.create(item)
except Exception as e:
    logger.error(f"Database error: {str(e)}", exc_info=True)
    raise InternalServerError("Failed to create item")
```

### 5. Use Specific Exceptions

```python
# Good
if user.balance < amount:
    raise PaymentRequiredError("Insufficient balance")

# Avoid - generic
if user.balance < amount:
    raise BadRequestError("Error")
```

### 6. Clean Up Resources

```python
# Good
def process_file(file: FileUpload):
    temp_path = None
    try:
        temp_path = save_temp_file(file)
        result = process(temp_path)
        return result
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        raise InternalServerError("File processing failed")
    finally:
        if temp_path:
            os.remove(temp_path)
```

### 7. Don't Swallow Exceptions

```python
# Good
try:
    risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {str(e)}")
    raise

# Avoid
try:
    risky_operation()
except:
    pass  # Silent failure
```

## Error Response Examples

### 400 Bad Request

```json
{
  "error": {
    "type": "bad_request",
    "message": "Invalid date format. Expected YYYY-MM-DD",
    "status": 400
  }
}
```

### 401 Unauthorized

```json
{
  "error": {
    "type": "authentication_error",
    "message": "Invalid or expired token",
    "status": 401
  }
}
```

### 403 Forbidden

```json
{
  "error": {
    "type": "authorization_error",
    "message": "You don't have permission to delete this resource",
    "status": 403
  }
}
```

### 404 Not Found

```json
{
  "error": {
    "type": "resource_not_found",
    "message": "User with ID 123 not found",
    "status": 404
  }
}
```

### 409 Conflict

```json
{
  "error": {
    "type": "resource_conflict",
    "message": "A user with this email already exists",
    "status": 409,
    "details": {
      "email": "user@example.com"
    }
  }
}
```

### 422 Validation Error

```json
{
  "error": {
    "type": "validation_error",
    "message": "Validation error",
    "status": 422,
    "details": [
      {
        "loc": ["body", "price"],
        "msg": "Input should be greater than 0",
        "type": "greater_than"
      }
    ]
  }
}
```

### 500 Internal Server Error

```json
{
  "error": {
    "type": "internal_server_error",
    "message": "An unexpected error occurred",
    "status": 500
  }
}
```

### 503 Service Unavailable

```json
{
  "error": {
    "type": "service_unavailable",
    "message": "Database is temporarily unavailable. Please try again later",
    "status": 503
  }
}
```

## Next Steps

- [Security](security.md) - Handle authentication errors
- [Validation](validation.md) - Understand validation errors
- [Dependencies](dependencies.md) - Error handling in dependencies
- [Testing](../advanced/testing.md) - Test error scenarios
