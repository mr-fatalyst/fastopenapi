# API Reference

This section provides a detailed reference for FastOpenAPI classes and modules, covering interfaces, methods, and specific usage examples.

## File Structure

FastOpenAPI follows a modular architecture:

```
fastopenapi/
├── base_router.py
└── routers/
    ├── aiohttp.py
    ├── falcon.py
    ├── flask.py
    ├── quart.py
    ├── sanic.py
    ├── starlette.py
    ├── tornado.py
    └── django.py
```

---

## BaseRouter

**Description:** Abstract base class providing common routing and OpenAPI schema generation functionality. Usually not instantiated directly, but inherited by framework-specific routers.

### Key Methods

- `__init__(app, docs_url="/docs", redoc_url="/redoc", openapi_url="/openapi.json", openapi_version="3.0.0", title="My App", version="0.1.0", description="API documentation")`
- `get(path, **options)`: Defines a GET route.
- `post(path, **options)`: Defines a POST route.
- `put(path, **options)`: Defines a PUT route.
- `patch(path, **options)`: Defines a PATCH route.
- `delete(path, **options)`: Defines a DELETE route.
- `include_router(other_router, prefix="")`: Includes another router's endpoints under a prefix.
- `generate_openapi_schema()`: Generates OpenAPI schema.

### Attributes

- `app`: Framework-specific application instance.
- `docs_url`, `redoc_url`, `openapi_url`: URLs for documentation endpoints.
- `title`, `description`, `version`: Metadata for OpenAPI schema.

---

## Framework Routers

Each router class inherits from `BaseRouter` and integrates with a specific framework.

### AioHttpRouter

Use for AIOHTTP integration.

```python
from aiohttp import web
from fastopenapi.routers import AioHttpRouter

app = web.Application()
router = AioHttpRouter(app=app)

@router.get("/status")
async def status():
    return {"status": "ok"}
```

---

### FalconRouter

Use for Falcon ASGI integration.

```python
import falcon.asgi
from fastopenapi.routers import FalconRouter

app = falcon.asgi.App()
router = FalconRouter(app=app)

@router.get("/status")
async def status():
    return {"status": "ok"}
```

---

### FlaskRouter

Use for Flask integration.

```python
from flask import Flask
from fastopenapi.routers import FlaskRouter

app = Flask(__name__)
router = FlaskRouter(app=app)

@router.get("/hello")
def hello(name: str):
    return {"message": f"Hello {name}"}
```

---

### QuartRouter

Use for Quart integration (async).

```python
from quart import Quart
from fastopenapi.routers import QuartRouter

app = Quart(__name__)
router = QuartRouter(app=app)

@router.get("/ping")
async def ping():
    return {"pong": True}
```

---

### SanicRouter

Use for Sanic integration.

```python
from sanic import Sanic
from fastopenapi.routers import SanicRouter

app = Sanic("MySanicApp")
router = SanicRouter(app=app)

@router.get("/info")
async def info():
    return {"framework": "Sanic", "status": "running"}
```

---

### StarletteRouter

Use for Starlette integration.

```python
from starlette.applications import Starlette
from fastopenapi.routers import StarletteRouter

app = Starlette()
router = StarletteRouter(app=app)

@router.get("/check")
async def check():
    return {"status": "healthy"}
```

---

### TornadoRouter

Use for Tornado integration.

```python
from tornado.web import Application
from fastopenapi.routers import TornadoRouter

app = Application()
router = TornadoRouter(app=app)

@router.get("/status")
def status():
    return {"running": True}
```

---

### DjangoRouter

Use for Django integration.

```python
from django.urls import path
from fastopenapi.routers import DjangoRouter

router = DjangoRouter(app=True)

@router.get("/status")
async def status():
    return {"status": "ok"}

urlpatterns = [path("", router.urls)]
```

---

### Example with Sub-router

```python
api_v1 = <Framework>Router()

@api_v1.get("/users")
def users():
    return [{"name": "Alice"}, {"name": "Bob"}]

main_router = <Framework>Router(app=app)
main_router.include_router(api_v1, prefix="/v1")
```

## Exception Handling

### Built-in Exceptions

Use built-in exceptions for clear HTTP error responses.

```python
from fastopenapi.error_handler import BadRequestError, ResourceNotFoundError

@router.get("/validate")
def validate_input(param: int):
    if param < 0:
        raise BadRequestError("Parameter must be positive")

@router.get("/items/{item_id}")
def get_item(item_id: int):
    item = db.get(item_id)
    if item is None:
        raise ResourceNotFoundError(f"Item {item_id} not found")
```

### Framework-specific Exceptions

Use framework-specific exceptions if you do not want to use exceptions from FastOpenAPI.

#### AioHTTP

```python
from aiohttp import web

@router.get("/notfound")
def aiohttp_notfound():
    raise web.HTTPNotFound(reason="Not Found")
```

#### Falcon

```python
import falcon

@router.get("/notfound")
async def falcon_notfound():
    raise falcon.HTTPNotFound(title="Not Found", description="Falcon error")
```

#### Flask

```python
from flask import abort

@router.get("/notfound")
def flask_notfound():
    abort(404, description="Flask error")
```

#### Quart

```python
from quart import abort

@router.get("/notfound")
async def quart_notfound():
    abort(404, description="Quart error")
```

#### Sanic

```python
from sanic import NotFound

@router.get("/notfound")
async def sanic_notfound():
    raise NotFound()
```

#### Starlette

```python
from starlette.exceptions import HTTPException

@router.get("/notfound")
async def starlette_notfound():
    raise HTTPException(status_code=404, detail="Not Found")
```

#### Tornado

```python
from tornado.web import HTTPError

@router.get("/notfound")
async def tornado_notfound():
    raise HTTPError(status_code=404, reason="Not Found")
```

#### Django

```python
from django.http import Http404

