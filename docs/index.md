!!! warning "Beta Release — v1.0.0b1"
    You are viewing the documentation for **v1.0.0b1** (beta). The API is stable, but minor changes may occur before the final release. The last stable version is available [here](https://fastopenapi.fatalyst.dev/0.7/).

# FastOpenAPI

<p align="center">
  <img src="https://raw.githubusercontent.com/mr-fatalyst/fastopenapi/master/logo.png" alt="Logo">
</p>

<p align="center">
  <b>FastOpenAPI</b> is a library for generating and integrating OpenAPI schemas using Pydantic and various frameworks.
</p>

<p align="center">
  This project was inspired by <a href="https://fastapi.tiangolo.com/">FastAPI</a> and aims to provide a similar developer-friendly experience.
</p>

<p align="center">
  <img src="https://img.shields.io/github/license/mr-fatalyst/fastopenapi">
  <img src="https://github.com/mr-fatalyst/fastopenapi/actions/workflows/master.yml/badge.svg">
  <img src="https://codecov.io/gh/mr-fatalyst/fastopenapi/branch/master/graph/badge.svg?token=USHR1I0CJB">
  <img src="https://img.shields.io/pypi/v/fastopenapi">
  <img src="https://img.shields.io/pypi/pyversions/fastopenapi">
  <img src="https://static.pepy.tech/badge/fastopenapi" alt="PyPI Downloads">
</p>

---

## What is FastOpenAPI?

FastOpenAPI brings FastAPI-style developer experience to frameworks like Flask, Django, Starlette, AIOHTTP, and others. It provides:

- **Automatic OpenAPI schema generation** from your route definitions
- **Interactive API documentation** (Swagger UI and ReDoc)
- **Request validation** using Pydantic models
- **Response serialization** with type safety
- **Framework-agnostic approach** - use with your preferred web framework

Inspired by [FastAPI](https://fastapi.tiangolo.com/), FastOpenAPI aims to provide similar functionality for developers who need to work with existing frameworks or prefer not to adopt a full framework switch.

## Key Features

### Multi-Framework Support

FastOpenAPI supports 8 popular Python web frameworks out of the box:

- **AIOHTTP** - Async HTTP client/server framework
- **Django** - High-level web framework (sync and async)
- **Falcon** - Minimalist ASGI/WSGI framework (sync and async)
- **Flask** - Lightweight WSGI framework
- **Quart** - Async version of Flask
- **Sanic** - Async web framework built for speed
- **Starlette** - Lightweight ASGI framework
- **Tornado** - Async networking library

### FastAPI-Style API

Use familiar decorator-based routing and parameter declarations:

```python
from fastopenapi import Query, Path, Body
from fastopenapi.routers import FlaskRouter
from pydantic import BaseModel

router = FlaskRouter(app=app)

class User(BaseModel):
    name: str
    email: str

@router.get("/users/{user_id}")
def get_user(user_id: int = Path(..., description="User ID")):
    return {"user_id": user_id}

@router.post("/users", response_model=User)
def create_user(user: User = Body(...)):
    return user
```

### Automatic Documentation

Once configured, your API documentation is automatically available:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

### Pydantic v2 Integration

Leverage Pydantic v2 for:

- Request body validation
- Response model validation
- Automatic JSON Schema generation
- Type coercion and error messages

### Advanced Features

**Dependency Injection**
```python
from fastopenapi import Depends

def get_db():
    db = Database()
    try:
        yield db
    finally:
        db.close()

@router.get("/items")
def list_items(db = Depends(get_db)):
    return db.get_items()
```

**Security Schemes**
```python
from fastopenapi import Security, SecuritySchemeType

router = FlaskRouter(
    app=app,
    security_scheme=SecuritySchemeType.BEARER_JWT
)

@router.get("/protected")
def protected_endpoint(token: str = Security(verify_token)):  # Your auth function
    return {"message": "Access granted"}
```

**File Uploads**
```python
from fastopenapi import File, FileUpload

@router.post("/upload")
async def upload_file(file: FileUpload = File(...)):
    content = await file.aread()
    return {"filename": file.filename, "size": len(content)}
```

## Project Status

FastOpenAPI is currently in **beta** (version 1.0.0b1). The API is stable, but minor changes may occur before the 1.0.0 release. We welcome feedback and contributions to help improve the library.

## Quick Example

Here's a complete working example with Flask:

```python
from flask import Flask
from pydantic import BaseModel
from fastopenapi.routers import FlaskRouter

app = Flask(__name__)
router = FlaskRouter(app=app, title="My API", version="1.0.0")

class Item(BaseModel):
    name: str
    price: float
    description: str | None = None

@router.get("/")
def root():
    return {"message": "Hello, FastOpenAPI!"}

@router.post("/items", response_model=Item, status_code=201)
def create_item(item: Item):
    return item

if __name__ == "__main__":
    app.run(port=8000)
```

Run the app and visit `http://localhost:8000/docs` to see your interactive API documentation.

## When to Use FastOpenAPI

**Use FastOpenAPI when:**

- You have an existing application in Flask, Django, or another supported framework
- You need OpenAPI documentation without switching frameworks
- You want FastAPI-style DX but can't use FastAPI
- You're building a library that needs to support multiple frameworks
- You prefer the flexibility of choosing your own framework

**Consider FastAPI when:**

- You're starting a new project from scratch
- You want a complete, batteries-included async framework
- You need built-in features like background tasks, WebSockets, and GraphQL support
- You need maximum performance with ASGI and modern async features
- You want the largest ecosystem, extensive documentation, and active community

## Next Steps

Ready to get started? Head over to:

- [Installation](getting_started/installation.md) - Install FastOpenAPI
- [Quickstart](getting_started/quickstart.md) - Build your first API in 5 minutes
- [Core Concepts](getting_started/core_concepts.md) - Understand the basics
- [User Guide](guide/routing.md) - Learn all the features

## Community and Support

- **GitHub**: [mr-fatalyst/fastopenapi](https://github.com/mr-fatalyst/fastopenapi)
- **Issues**: [Report bugs or request features](https://github.com/mr-fatalyst/fastopenapi/issues)
- **Discussions**: [Ask questions and share ideas](https://github.com/mr-fatalyst/fastopenapi/discussions)

## License

FastOpenAPI is licensed under the MIT License. See the [LICENSE](https://github.com/mr-fatalyst/fastopenapi/blob/master/LICENSE) file for details.

