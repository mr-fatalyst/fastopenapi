# Request Parameters

This guide covers how to extract and validate parameters from requests using FastOpenAPI's parameter classes.

## Overview

FastOpenAPI provides several parameter types for extracting data from different parts of the request:

- `Path(...)` - URL path parameters
- `Query(...)` - Query string parameters
- `Header(...)` - HTTP headers
- `Cookie(...)` - HTTP cookies

These classes provide validation, documentation, and type conversion.

## Query Parameters

Query parameters come from the URL query string (`?param=value`).

### Basic Query Parameters

```python
from fastopenapi import Query

@router.get("/items")
def list_items(
    skip: int = Query(0, description="Number of items to skip"),
    limit: int = Query(10, description="Maximum number of items")
):
    return {"skip": skip, "limit": limit}

# GET /items?skip=20&limit=50
```

### Optional Query Parameters

```python
@router.get("/search")
def search(
    q: str | None = Query(None, description="Search query"),
    category: str | None = Query(None, description="Filter by category")
):
    if q:
        return {"searching_for": q, "category": category}
    return {"message": "No search query provided"}

# GET /search?q=laptop&category=electronics
```

### Required Query Parameters

```python
@router.get("/search")
def search(
    q: str = Query(..., description="Search query (required)")
):
    return {"searching_for": q}

# GET /search          -> 422 error
# GET /search?q=laptop -> OK
```

### Query Parameter Validation

```python
@router.get("/items")
def list_items(
    skip: int = Query(0, ge=0, description="Must be >= 0"),
    limit: int = Query(10, ge=1, le=100, description="Between 1 and 100")
):
    return {"skip": skip, "limit": limit}

# GET /items?skip=-1&limit=200 -> 422 error
```

**Validation constraints:**

- `ge` - Greater than or equal
- `le` - Less than or equal
- `gt` - Greater than
- `lt` - Less than
- `min_length` - Minimum string length
- `max_length` - Maximum string length
- `pattern` - Regular expression pattern

### Multiple Values

```python
@router.get("/items")
def filter_items(
    tags: list[str] = Query([], description="Filter by tags")
):
    return {"tags": tags}

# GET /items?tags=new&tags=featured&tags=sale
# Returns: {"tags": ["new", "featured", "sale"]}
```

### Default Values

```python
@router.get("/items")
def list_items(
    sort: str = Query("created_at", description="Sort field"),
    order: str = Query("desc", description="Sort order")
):
    return {"sort": sort, "order": order}

# GET /items                         -> sort="created_at", order="desc"
# GET /items?sort=name&order=asc     -> sort="name", order="asc"
```

### Aliasing

Use different names in code vs. URL:

```python
@router.get("/items")
def list_items(
    items_per_page: int = Query(10, alias="per_page")
):
    return {"items_per_page": items_per_page}

# GET /items?per_page=50
```

## Path Parameters

Path parameters are extracted from the URL path.

### Basic Path Parameters

```python
from fastopenapi import Path

@router.get("/users/{user_id}")
def get_user(user_id: int = Path(..., description="User ID")):
    return {"user_id": user_id}

# GET /users/123
```

### Path Parameter Validation

```python
@router.get("/items/{item_id}")
def get_item(
    item_id: int = Path(..., ge=1, description="Item ID must be positive")
):
    return {"item_id": item_id}

# GET /items/0  -> 422 error
# GET /items/1  -> OK
```

### Multiple Path Parameters

```python
@router.get("/users/{user_id}/posts/{post_id}")
def get_user_post(
    user_id: int = Path(..., description="User ID"),
    post_id: int = Path(..., description="Post ID")
):
    return {"user_id": user_id, "post_id": post_id}

# GET /users/123/posts/456
```

### String Path Parameters

```python
@router.get("/categories/{category_name}")
def get_category(
    category_name: str = Path(
        ..., 
        min_length=2,
        max_length=50,
        description="Category name"
    )
):
    return {"category": category_name}

# GET /categories/electronics
```

### Path with Query Parameters

Combine path and query parameters:

```python
@router.get("/users/{user_id}/posts")
def get_user_posts(
    user_id: int = Path(..., description="User ID"),
    limit: int = Query(10, description="Number of posts"),
    offset: int = Query(0, description="Offset")
):
    return {
        "user_id": user_id,
        "limit": limit,
        "offset": offset
    }

# GET /users/123/posts?limit=5&offset=10
```

## Header Parameters

Extract data from HTTP headers.

### Basic Headers

```python
from fastopenapi import Header

@router.get("/items")
def list_items(
    user_agent: str | None = Header(None, alias="User-Agent")
):
    return {"user_agent": user_agent}
```

**Note:** Header names are case-insensitive in HTTP, but use kebab-case in the `alias`.

### Required Headers

```python
@router.get("/protected")
def protected_endpoint(
    api_key: str = Header(..., alias="X-API-Key")
):
    if api_key != "secret":
        raise AuthorizationError("Invalid API key")
    return {"message": "Access granted"}

# GET /protected
# Headers: X-API-Key: secret
```

### Common Headers

```python
@router.post("/items")
def create_item(
    content_type: str = Header(..., alias="Content-Type"),
    content_length: int | None = Header(None, alias="Content-Length"),
    authorization: str | None = Header(None, alias="Authorization")
):
    return {
        "content_type": content_type,
        "content_length": content_length
    }
```

### Custom Headers

```python
@router.get("/items")
def list_items(
    request_id: str = Header(..., alias="X-Request-ID"),
    correlation_id: str | None = Header(None, alias="X-Correlation-ID")
):
    return {
        "request_id": request_id,
        "correlation_id": correlation_id
    }
```

## Cookie Parameters

Extract data from cookies.

### Basic Cookies

```python
from fastopenapi import Cookie

@router.get("/items")
def list_items(
    session_id: str | None = Cookie(None, description="Session ID")
):
    return {"session_id": session_id}
```

### Required Cookies

```python
@router.get("/profile")
def get_profile(
    session_token: str = Cookie(..., description="Session token required")
):
    # Validate session token
    user = validate_session(session_token)
    return {"user": user}
```

### Multiple Cookies

```python
@router.get("/dashboard")
def dashboard(
    session_id: str = Cookie(...),
    preferences: str | None = Cookie(None),
    theme: str = Cookie("light")
):
    return {
        "session_id": session_id,
        "preferences": preferences,
        "theme": theme
    }
```

## Combining Parameter Types

You can use all parameter types together:

```python
from fastopenapi import Path, Query, Header, Cookie

@router.get("/users/{user_id}/posts/{post_id}")
def get_post(
    # Path parameters
    user_id: int = Path(..., description="User ID"),
    post_id: int = Path(..., description="Post ID"),
    
    # Query parameters
    include_comments: bool = Query(False, description="Include comments"),
    
    # Headers
    accept_language: str = Header("en", alias="Accept-Language"),
    
    # Cookies
    session_id: str | None = Cookie(None)
):
    return {
        "user_id": user_id,
        "post_id": post_id,
        "include_comments": include_comments,
        "language": accept_language,
        "session_id": session_id
    }
```

## Type Conversion

FastOpenAPI automatically converts parameter values:

```python
@router.get("/convert")
def convert_types(
    integer: int = Query(...),
    floating: float = Query(...),
    boolean: bool = Query(...),
    string: str = Query(...)
):
    return {
        "integer": integer,       # "123" -> 123
        "floating": floating,     # "1.5" -> 1.5
        "boolean": boolean,       # "true" -> True, "1" -> True
        "string": string          # No conversion
    }

# GET /convert?integer=123&floating=1.5&boolean=true&string=hello
```

### Boolean Conversion

The following values are converted to `True`:

- `true`, `True`, `TRUE`
- `1`, `yes`, `on`

The following values are converted to `False`:

- `false`, `False`, `FALSE`
- `0`, `no`, `off`

## Pydantic Model Parameters

Use Pydantic models for complex query parameters:

```python
from pydantic import BaseModel, Field

class Pagination(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(10, ge=1, le=100, description="Items per page")

class Filters(BaseModel):
    category: str | None = None
    min_price: float | None = Field(None, ge=0)
    max_price: float | None = Field(None, ge=0)
    in_stock: bool = True

@router.get("/items")
def list_items(
    pagination: Pagination = Query(...),
    filters: Filters = Query(...)
):
    return {
        "page": pagination.page,
        "per_page": pagination.per_page,
        "filters": filters.model_dump(exclude_none=True)
    }

# GET /items?page=2&per_page=20&category=electronics&min_price=100
```

## Documentation and Examples

### Adding Descriptions

```python
@router.get("/items")
def list_items(
    search: str = Query(
        None,
        description="Search items by name or description",
        example="laptop"
    ),
    min_price: float = Query(
        0,
        description="Minimum price filter",
        example=99.99
    )
):
    return {}
```

### Deprecated Parameters

Mark parameters as deprecated:

```python
@router.get("/items")
def list_items(
    old_filter: str | None = Query(
        None,
        deprecated=True,
        description="Use 'search' parameter instead"
    ),
    search: str | None = Query(None, description="Search query")
):
    # Handle backwards compatibility
    query = search or old_filter
    return {"query": query}
```

## Validation Examples

### Email Validation

```python
from pydantic import EmailStr

@router.get("/users")
def find_user(
    email: EmailStr = Query(..., description="User email")
):
    return {"email": email}

# GET /users?email=invalid -> 422 error
# GET /users?email=user@example.com -> OK
```

### Enum Validation

```python
from enum import Enum

class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"

@router.get("/items")
def list_items(
    sort: SortOrder = Query(SortOrder.desc, description="Sort order")
):
    return {"sort": sort.value}

# GET /items?sort=asc  -> OK
# GET /items?sort=invalid -> 422 error
```

### Date Validation

```python
from datetime import date

@router.get("/events")
def list_events(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date | None = Query(None, description="End date")
):
    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat() if end_date else None
    }

# GET /events?start_date=2024-01-01&end_date=2024-12-31
```

## Error Handling

### Validation Errors

When parameters fail validation, FastOpenAPI returns a 422 error:

```http
GET /items?limit=-5

HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json

{
  "error": {
    "type": "validation_error",
    "message": "Error parsing parameter 'limit'",
    "status": 422,
    "details": "Input should be greater than or equal to 1"
  }
}
```

### Missing Required Parameters

```http
GET /search

HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json

{
  "error": {
    "type": "validation_error",
    "message": "Missing required parameter: 'q'",
    "status": 422
  }
}
```

> **Note:** For missing parameters, the `details` field is omitted. For validation failures, `details` contains a string description of the error.

## Best Practices

### 1. Use Type Hints

```python
# Good
def list_items(limit: int = Query(10)):
    pass

# Avoid
def list_items(limit = Query(10)):
    pass
```

### 2. Provide Descriptions

```python
# Good
limit: int = Query(10, description="Maximum number of items to return")

# Avoid
limit: int = Query(10)
```

### 3. Set Sensible Defaults

```python
# Good
limit: int = Query(20, ge=1, le=100)

# Avoid (unbounded)
limit: int = Query(999999)
```

### 4. Use Validation Constraints

```python
# Good - prevents abuse
page: int = Query(1, ge=1, le=1000)

# Risky - no limits
page: int = Query(1)
```

### 5. Group Related Parameters

```python
# Good - using a model
class SearchParams(BaseModel):
    query: str
    category: str | None
    min_price: float

# Instead of many individual parameters
```

## Next Steps

- [Request Body](request_body.md) - Handle JSON, forms, and files
- [Response Handling](response_handling.md) - Customize responses
- [Validation](validation.md) - Advanced Pydantic validation
- [Dependencies](dependencies.md) - Dependency injection for parameters
