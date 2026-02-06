# Core Concepts

This guide explains the fundamental concepts behind FastOpenAPI and how it works.

## What is OpenAPI?

**OpenAPI** (formerly Swagger) is a specification for describing RESTful APIs. An OpenAPI document describes:

- Available endpoints (paths)
- HTTP methods for each endpoint (GET, POST, etc.)
- Request parameters (path, query, header, body)
- Response formats and status codes
- Authentication methods
- Data models and schemas

OpenAPI documents are machine-readable, which enables:

- **Automatic documentation generation** - Tools like Swagger UI and ReDoc
- **Code generation** - Generate client libraries in multiple languages
- **API validation** - Ensure requests and responses match the specification
- **Testing** - Automated API testing tools

## How FastOpenAPI Works

FastOpenAPI acts as a bridge between your web framework and OpenAPI documentation:

```
Your Framework (Flask, Django, etc.)
         |
         v
   FastOpenAPI Router
    - Registers routes
    - Validates requests
    - Generates OpenAPI schema
         |
         v
    Automatic Docs
    (Swagger UI, ReDoc)
```

### The Flow

1. **You define routes** using FastOpenAPI decorators
2. **FastOpenAPI registers** routes with your framework
3. **When a request comes in**, FastOpenAPI:
   - Extracts parameters from the request
   - Validates them against Pydantic models
   - Calls your endpoint function
   - Validates and serializes the response
4. **OpenAPI schema is generated** from your route definitions
5. **Documentation UIs** consume the schema to create interactive docs

## Key Components

### 1. Router

The router is the main interface to FastOpenAPI. Each framework has its own router class:

```python
from fastopenapi.routers import FlaskRouter

router = FlaskRouter(
    app=app,                    # Your framework's app instance
    title="My API",             # API title for docs
    version="1.0.0",            # API version
    description="API docs",     # Description
    docs_url="/docs",           # Swagger UI URL
    redoc_url="/redoc",         # ReDoc URL
    openapi_url="/openapi.json" # OpenAPI schema URL
)
```

The router provides decorators for defining routes:

```python
@router.get("/items/{item_id}")
@router.post("/items")
@router.put("/items/{item_id}")
@router.patch("/items/{item_id}")
@router.delete("/items/{item_id}")
```

### 2. Request Parameters

FastOpenAPI uses special classes to define where parameters come from:

```python
from fastopenapi import Query, Path, Header, Cookie, Body

@router.get("/items/{item_id}")
def get_item(
    item_id: int = Path(..., description="The item ID"),
    search: str = Query(None, description="Search query"),
    user_agent: str = Header(None, alias="User-Agent")
):
    return {"item_id": item_id, "search": search}
```

**Parameter Types:**

- `Path(...)` - From URL path (`/items/{item_id}`)
- `Query(...)` - From query string (`?search=value`)
- `Header(...)` - From HTTP headers
- `Cookie(...)` - From cookies
- `Body(...)` - From request body (JSON, form, etc.)

### 3. Pydantic Models

[Pydantic](https://docs.pydantic.dev/) is used for:

- Request body validation
- Response serialization
- Automatic JSON Schema generation

```python
from pydantic import BaseModel, Field

class Item(BaseModel):
    name: str = Field(..., description="Item name")
    price: float = Field(..., gt=0, description="Price must be positive")
    description: str | None = None

@router.post("/items", response_model=Item)
def create_item(item: Item = Body(...)):
    # item is already validated
    return item
```

**Benefits:**

- **Type safety** - Python type hints enforced at runtime
- **Automatic validation** - Invalid data returns 422 error with details
- **Data coercion** - Strings converted to ints, floats, etc.
- **Schema generation** - JSON Schema created automatically

### 4. Response Models

Response models ensure your endpoints return the correct structure:

```python
class UserResponse(BaseModel):
    id: int
    username: str
    email: str

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    user = database.get_user(user_id)
    # Response is validated against UserResponse
    return user
```

**What happens:**

1. Your function returns data (dict, model instance, etc.)
2. FastOpenAPI validates it against `response_model`
3. Invalid responses raise `InternalServerError` (500)
4. Valid responses are serialized to JSON

### 5. Status Codes

Specify the success status code for each endpoint:

```python
@router.post("/items", status_code=201)  # Created
def create_item(item: Item):
    return item

@router.delete("/items/{item_id}", status_code=204)  # No Content
def delete_item(item_id: int):
    database.delete(item_id)
    return None
```

Common status codes:

- `200` - OK (default)
- `201` - Created (for POST)
- `204` - No Content (for DELETE)
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error

### 6. Tags

Group endpoints in the documentation:

```python
@router.get("/users", tags=["Users"])
def list_users():
    return []

@router.get("/items", tags=["Items"])
def list_items():
    return []
```

Tags appear as sections in Swagger UI and ReDoc.

## Request Lifecycle

Let's follow a request through FastOpenAPI:

```python
@router.post("/items", response_model=Item, status_code=201)
def create_item(
    item: Item = Body(...),
    api_key: str = Header(..., alias="X-API-Key")
):
    return item
```

**1. Request arrives:**
```http
POST /items HTTP/1.1
X-API-Key: secret123
Content-Type: application/json

{"name": "Widget", "price": 9.99}
```

**2. Framework routes to FastOpenAPI handler**

**3. FastOpenAPI extracts parameters:**
- Body: `{"name": "Widget", "price": 9.99}`
- Header: `X-API-Key: secret123`

**4. Validation:**
- Body validated against `Item` model
- Header validated as string
- If invalid, returns 422 error immediately

**5. Your function is called:**
```python
create_item(
    item=Item(name="Widget", price=9.99),
    api_key="secret123"
)
```

**6. Response validation:**
- Return value validated against `Item` model
- If invalid, returns 500 error

**7. Serialization:**
- Model converted to dict
- Dict converted to JSON

**8. HTTP response:**
```http
HTTP/1.1 201 Created
Content-Type: application/json

{"name": "Widget", "price": 9.99, "description": null}
```

## Validation Errors

When validation fails, FastOpenAPI returns a detailed error:

**Invalid request:**
```json
POST /items
{"name": "Widget", "price": -5}
```

**Error response:**
```json
HTTP/1.1 422 Unprocessable Entity

{
  "error": {
    "type": "validation_error",
    "message": "Validation error",
    "status": 422,
    "details": [
      {
        "loc": ["price"],
        "msg": "Input should be greater than 0",
        "type": "greater_than"
      }
    ]
  }
}
```

## Error Handling

FastOpenAPI provides standard exception classes:

```python
from fastopenapi.errors import (
    BadRequestError,
    ResourceNotFoundError,
    AuthorizationError
)

@router.get("/items/{item_id}")
def get_item(item_id: int):
    item = database.get(item_id)
    if not item:
        raise ResourceNotFoundError(f"Item {item_id} not found")
    return item
```

**Built-in exceptions:**

- `BadRequestError` - 400
- `AuthenticationError` - 401
- `AuthorizationError` - 403
- `ResourceNotFoundError` - 404
- `ResourceConflictError` - 409
- `ValidationError` - 422
- `InternalServerError` - 500
- `ServiceUnavailableError` - 503

## Framework-Agnostic Design

FastOpenAPI is designed to work with multiple frameworks by:

1. **Abstracting request/response handling**
   - Each framework has an adapter
   - Adapters convert framework-specific objects to unified types

2. **Using Pydantic for validation**
   - Framework-independent validation logic
   - Same validation behavior across all frameworks

3. **Generating standard OpenAPI**
   - OpenAPI schema is framework-agnostic
   - Same documentation regardless of framework

This means you can:

- Switch frameworks with minimal code changes
- Use the same skills across different projects
- Build libraries that support multiple frameworks

## Sync vs Async

Some frameworks are synchronous (Flask, Django WSGI), others are asynchronous (Starlette, AIOHTTP).

**Synchronous example (Flask):**
```python
@router.get("/items/{item_id}")
def get_item(item_id: int):
    return {"item_id": item_id}
```

**Asynchronous example (Starlette):**
```python
@router.get("/items/{item_id}")
async def get_item(item_id: int):
    await asyncio.sleep(0.1)  # Some async operation
    return {"item_id": item_id}
```

FastOpenAPI handles both automatically:

- Sync routers call functions normally
- Async routers await async functions
- Mixing sync/async incorrectly raises an error

## Comparison with FastAPI

| Feature | FastAPI | FastOpenAPI |
|---------|---------|-------------|
| **Framework** | Complete framework | Library for existing frameworks |
| **Routing** | Built-in | Integrates with framework routing |
| **Validation** | Pydantic v2 | Pydantic v2 |
| **OpenAPI** | Auto-generated | Auto-generated |
| **Async** | ASGI only | Sync and async |
| **Dependencies** | Built-in DI | Built-in DI (new in 1.0) |
| **Learning curve** | Moderate | Low (if you know the framework) |
| **Best for** | New projects | Existing projects, multi-framework |

## Next Steps

Now that you understand the concepts, learn how to use them:

- [Routing](../guide/routing.md) - Define endpoints and HTTP methods
- [Request Parameters](../guide/request_parameters.md) - Path, query, header parameters
- [Request Body](../guide/request_body.md) - JSON, forms, files
- [Validation](../guide/validation.md) - Deep dive into Pydantic
- [Dependencies](../guide/dependencies.md) - Dependency injection system
- [Security](../guide/security.md) - Authentication and authorization
