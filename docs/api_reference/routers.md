# Routers API Reference

API reference for router classes in FastOpenAPI.

## Router Classes

FastOpenAPI provides router classes for each supported framework:

- `AioHttpRouter` - for aiohttp (async)
- `DjangoRouter` - for Django (sync)
- `DjangoAsyncRouter` - for Django (async)
- `FalconRouter` - for Falcon (sync)
- `FalconAsyncRouter` - for Falcon (async)
- `FlaskRouter` - for Flask (sync)
- `QuartRouter` - for Quart (async)
- `SanicRouter` - for Sanic (async)
- `StarletteRouter` - for Starlette (async)
- `TornadoRouter` - for Tornado (async/sync)

---

## BaseRouter

All framework routers inherit from `BaseRouter`.

### Constructor

```python
def __init__(
    self,
    app: Any = None,
    docs_url: str | None = "/docs",
    redoc_url: str | None = "/redoc",
    openapi_url: str | None = "/openapi.json",
    openapi_version: str = "3.0.0",
    title: str = "My App",
    version: str = "0.1.0",
    description: str = "API documentation",
    security_scheme: SecuritySchemeType | None = SecuritySchemeType.BEARER_JWT,
)
```

### Parameters

- **app**: Framework application instance
- **docs_url**: URL for Swagger UI docs (default: `"/docs"`)
- **redoc_url**: URL for ReDoc UI docs (default: `"/redoc"`)
- **openapi_url**: URL for OpenAPI JSON schema (default: `"/openapi.json"`)

> **Note:** Setting any of these to `None` disables all documentation endpoints (Swagger UI, ReDoc, and OpenAPI JSON) at once.
- **openapi_version**: OpenAPI specification version (default: `"3.0.0"`)
- **title**: API title
- **version**: API version
- **description**: API description
- **security_scheme**: Security scheme for OpenAPI docs (default: Bearer JWT)

### HTTP Method Decorators

#### get()

```python
@router.get(path: str, **meta)
```

Register GET endpoint.

**Parameters**:
- `path`: URL path (e.g., `/users/{user_id}`)
- `**meta`: Optional metadata
  - `response_model`: Pydantic model for response validation
  - `status_code`: HTTP status code (default: 200)
  - `tags`: List of tags for OpenAPI grouping
  - `summary`: Short summary for OpenAPI docs
  - `description`: Detailed description for OpenAPI docs
  - `deprecated`: Mark as deprecated (default: `False`)

**Example**:
```python
@router.get(
    "/users/{user_id}",
    response_model=User,
    tags=["Users"],
    summary="Get user by ID",
    description="Retrieve a single user by their ID"
)
def get_user(user_id: int):
    return {"id": user_id, "username": "john"}
```

#### post()

```python
@router.post(path: str, **meta)
```

Register POST endpoint (typically for creating resources).

**Example**:
```python
@router.post(
    "/users",
    response_model=User,
    status_code=201,
    tags=["Users"]
)
def create_user(user: UserCreate):
    return create_user_in_db(user)
```

#### put()

```python
@router.put(path: str, **meta)
```

Register PUT endpoint (typically for full updates).

**Example**:
```python
@router.put("/users/{user_id}", response_model=User)
def update_user(user_id: int, user: UserUpdate):
    return update_user_in_db(user_id, user)
```

#### patch()

```python
@router.patch(path: str, **meta)
```

Register PATCH endpoint (typically for partial updates).

**Example**:
```python
@router.patch("/users/{user_id}", response_model=User)
def partial_update_user(user_id: int, updates: UserPartialUpdate):
    return patch_user_in_db(user_id, updates)
```

#### delete()

```python
@router.delete(path: str, **meta)
```

Register DELETE endpoint.

**Example**:
```python
@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int):
    delete_user_from_db(user_id)
    return None
```

#### head()

```python
@router.head(path: str, **meta)
```

Register HEAD endpoint.

#### options()

```python
@router.options(path: str, **meta)
```

Register OPTIONS endpoint.

---

## Router Properties

### openapi

Get the OpenAPI schema (lazy-loaded).

```python
schema = router.openapi
```

Returns the complete OpenAPI 3.0 schema as a dictionary.

**Example**:
```python
from flask import Flask
from fastopenapi.routers import FlaskRouter

app = Flask(__name__)
router = FlaskRouter(app=app, title="My API", version="1.0.0")

@router.get("/items")
def list_items():
    return {"items": []}

# Get OpenAPI schema
schema = router.openapi
print(schema["info"]["title"])  # "My API"
print(schema["info"]["version"])  # "1.0.0"
```

---

## Router Methods

### add_route()

Manually add a route to the router.

```python
def add_route(self, path: str, method: str, endpoint: Callable)
```

**Parameters**:
- `path`: URL path
- `method`: HTTP method (`"GET"`, `"POST"`, etc.)
- `endpoint`: Handler function

**Example**:
```python
def my_handler():
    return {"message": "Hello"}

router.add_route("/hello", "GET", my_handler)
```

**Note**: Typically you use decorators instead of calling this directly.

### include_router()

Include routes from another router with an optional prefix.

```python
def include_router(self, other: BaseRouter, prefix: str = "")
```

**Parameters**:
- `other`: Router to include
- `prefix`: URL prefix for all routes from the other router

**Example**:
```python
from fastopenapi.routers import FlaskRouter

# Main router
main_router = FlaskRouter(app=app)

# Sub-router for users
users_router = FlaskRouter()

@users_router.get("/{user_id}")
def get_user(user_id: int):
    return {"user_id": user_id}

@users_router.post("/")
def create_user(username: str):
    return {"username": username}

# Include users router with prefix
main_router.include_router(users_router, prefix="/users")

# Now available at:
# GET /users/{user_id}
# POST /users/
```

### get_routes()

Get all registered routes.

```python
def get_routes(self) -> list[RouteInfo]
```

**Returns**: List of `RouteInfo` objects containing route metadata.

**Example**:
```python
routes = router.get_routes()
for route in routes:
    print(f"{route.method} {route.path}")
```

---

## Framework-Specific Routers

### FlaskRouter

```python
from flask import Flask
from fastopenapi.routers import FlaskRouter

app = Flask(__name__)
router = FlaskRouter(
    app=app,
    title="Flask API",
    version="1.0.0"
)

@router.get("/items")
def list_items():
    return {"items": []}

if __name__ == "__main__":
    app.run()
```

### StarletteRouter

```python
import uvicorn
from starlette.applications import Starlette
from fastopenapi.routers import StarletteRouter

app = Starlette()
router = StarletteRouter(
    app=app,
    title="Starlette API",
    version="1.0.0"
)

@router.get("/items")
async def list_items():
    return {"items": []}

if __name__ == "__main__":
    uvicorn.run(app)
```

### AioHttpRouter

```python
from aiohttp import web
from fastopenapi.routers import AioHttpRouter

app = web.Application()
router = AioHttpRouter(
    app=app,
    title="AioHTTP API",
    version="1.0.0"
)

@router.get("/items")
async def list_items():
    return {"items": []}

if __name__ == "__main__":
    web.run_app(app)
```

### SanicRouter

```python
from sanic import Sanic
from fastopenapi.routers import SanicRouter

app = Sanic("MyApp")
router = SanicRouter(
    app=app,
    title="Sanic API",
    version="1.0.0"
)

@router.get("/items")
async def list_items():
    return {"items": []}

if __name__ == "__main__":
    app.run()
```

### QuartRouter

```python
from quart import Quart
from fastopenapi.routers import QuartRouter

app = Quart(__name__)
router = QuartRouter(
    app=app,
    title="Quart API",
    version="1.0.0"
)

@router.get("/items")
async def list_items():
    return {"items": []}

if __name__ == "__main__":
    app.run()
```

### FalconRouter / FalconAsyncRouter

```python
from falcon import App
from fastopenapi.routers import FalconRouter

app = App()
router = FalconRouter(
    app=app,
    title="Falcon API",
    version="1.0.0"
)

@router.get("/items")
def list_items():
    return {"items": []}

# For async Falcon:
# from fastopenapi.routers import FalconAsyncRouter
# router = FalconAsyncRouter(app=app)
```

### DjangoRouter / DjangoAsyncRouter

Django doesn't have a typical application object like other frameworks. Pass `app=True` to enable documentation endpoint registration (this satisfies the internal `app is not None` check):

```python
from django.urls import path
from fastopenapi.routers import DjangoRouter

router = DjangoRouter(app=True)

@router.get("/items")
def list_items():
    return {"items": []}

urlpatterns = [path("", router.urls)]

# For async Django:
# from fastopenapi.routers import DjangoAsyncRouter
# router = DjangoAsyncRouter(app=True)
```

### TornadoRouter

```python
import asyncio
from tornado.web import Application
from fastopenapi.routers import TornadoRouter

app = Application()
router = TornadoRouter(
    app=app,
    title="Tornado API",
    version="1.0.0"
)

@router.get("/items")
async def list_items():
    return {"items": []}

async def main():
    app.listen(8000)
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Security Schemes

Set the security scheme for OpenAPI documentation:

```python
from fastopenapi.core.constants import SecuritySchemeType

# Bearer JWT (default)
router = FlaskRouter(
    app=app,
    security_scheme=SecuritySchemeType.BEARER_JWT
)

# API Key in header
router = FlaskRouter(
    app=app,
    security_scheme=SecuritySchemeType.API_KEY_HEADER
)

# API Key in query
router = FlaskRouter(
    app=app,
    security_scheme=SecuritySchemeType.API_KEY_QUERY
)

# Basic Auth
router = FlaskRouter(
    app=app,
    security_scheme=SecuritySchemeType.BASIC_AUTH
)

# OAuth2
router = FlaskRouter(
    app=app,
    security_scheme=SecuritySchemeType.OAUTH2
)

# No security scheme
router = FlaskRouter(
    app=app,
    security_scheme=None
)
```

---

## Documentation URLs

### Customizing Documentation URLs

```python
router = FlaskRouter(
    app=app,
    docs_url="/api/docs",           # Swagger UI
    redoc_url="/api/redoc",         # ReDoc
    openapi_url="/api/openapi.json" # OpenAPI schema
)
```

### Disabling Documentation

To disable all documentation endpoints, set any URL to `None`:

```python
router = FlaskRouter(
    app=app,
    docs_url=None,      # Disables all: Swagger UI, ReDoc, and OpenAPI JSON
)
```

---

## Route Metadata

### Tags

Group endpoints in documentation:

```python
@router.get("/users", tags=["Users"])
def list_users():
    return []

@router.get("/posts", tags=["Posts"])
def list_posts():
    return []
```

### Summary and Description

```python
@router.get(
    "/users/{user_id}",
    summary="Get user by ID",
    description="Retrieve detailed information about a specific user",
    tags=["Users"]
)
def get_user(user_id: int):
    return {"id": user_id}
```

### Deprecated

```python
@router.get(
    "/old-endpoint",
    deprecated=True,
    description="This endpoint is deprecated. Use /new-endpoint instead."
)
def old_endpoint():
    return {"message": "Deprecated"}
```

---

## Best Practices

### 1. Use App Instance

```python
# Good - pass app to router
app = Flask(__name__)
router = FlaskRouter(app=app)

# Avoid - creating router without app
router = FlaskRouter()
```

### 2. Organize with Tags

```python
@router.get("/users", tags=["Users"])
@router.get("/posts", tags=["Posts"])
@router.get("/comments", tags=["Comments"])
```

### 3. Use Sub-Routers

```python
# users_router.py
users_router = FlaskRouter()

@users_router.get("/{user_id}")
def get_user(user_id: int):
    return {"id": user_id}

# main.py
from users_router import users_router

main_router = FlaskRouter(app=app)
main_router.include_router(users_router, prefix="/users")
```

### 4. Set Appropriate Metadata

```python
router = FlaskRouter(
    app=app,
    title="My Production API",
    version="2.1.0",
    description="Comprehensive API for managing resources"
)
```

---

## See Also

- [Routing Guide](../guide/routing.md) - Routing patterns
- [Framework Guides](../frameworks/overview.md) - Framework-specific guides
- [OpenAPI Customization](../advanced/openapi_customization.md) - Customizing OpenAPI docs
- [Security Guide](../guide/security.md) - Security configuration
