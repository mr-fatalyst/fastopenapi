# Quickstart

This quickstart guide will help you create your first FastOpenAPI application in just a few minutes.

## Choose Your Framework

Select your preferred framework to see a working example:

- [Flask](#flask-example)
- [Starlette](#starlette-example)
- [Django](#django-example)
- [AIOHTTP](#aiohttp-example)
- [Falcon](#falcon-example)
- [Quart](#quart-example)
- [Sanic](#sanic-example)
- [Tornado](#tornado-example)

## Flask Example

### Step 1: Install

```bash
pip install fastopenapi[flask]
```

### Step 2: Create `main.py`

```python
from flask import Flask
from pydantic import BaseModel
from fastopenapi.routers import FlaskRouter

# Create Flask app
app = Flask(__name__)

# Create FastOpenAPI router
router = FlaskRouter(
    app=app,
    title="My Flask API",
    version="1.0.0",
    description="A simple API built with Flask and FastOpenAPI"
)

# Define a Pydantic model
class Item(BaseModel):
    name: str
    price: float
    description: str | None = None

# Define routes
@router.get("/")
def root():
    """Root endpoint"""
    return {"message": "Hello from Flask!"}

@router.get("/items/{item_id}")
def get_item(item_id: int):
    """Get an item by ID"""
    return {"item_id": item_id, "name": f"Item {item_id}"}

@router.post("/items", response_model=Item, status_code=201)
def create_item(item: Item):
    """Create a new item"""
    return item

if __name__ == "__main__":
    app.run(port=8000, debug=True)
```

### Step 3: Run

```bash
python main.py
```

### Step 4: Test

Open your browser and visit:

- API: `http://localhost:8000/items/1`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Starlette Example

### Step 1: Install

```bash
pip install fastopenapi[starlette] uvicorn
```

### Step 2: Create `main.py`

```python
import uvicorn
from starlette.applications import Starlette
from pydantic import BaseModel
from fastopenapi.routers import StarletteRouter

# Create Starlette app
app = Starlette()

# Create FastOpenAPI router
router = StarletteRouter(
    app=app,
    title="My Starlette API",
    version="1.0.0"
)

class Item(BaseModel):
    name: str
    price: float

@router.get("/")
async def root():
    return {"message": "Hello from Starlette!"}

@router.get("/items/{item_id}")
async def get_item(item_id: int):
    return {"item_id": item_id}

@router.post("/items", response_model=Item, status_code=201)
async def create_item(item: Item):
    return item

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

### Step 3: Run

```bash
python main.py
```

Or use uvicorn directly:

```bash
uvicorn main:app --reload
```

---

## Django Example

### Step 1: Install

```bash
pip install fastopenapi[django]
```

### Step 2: Create `main.py`

```python
from django.conf import settings
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application
from django.urls import path
from pydantic import BaseModel
from fastopenapi.routers import DjangoRouter

# Configure Django settings
settings.configure(
    DEBUG=True,
    SECRET_KEY="your-secret-key-here",
    ROOT_URLCONF=__name__,
    ALLOWED_HOSTS=["*"],
)

# Initialize Django
application = get_wsgi_application()

# Create FastOpenAPI router
router = DjangoRouter(
    app=True,
    title="My Django API",
    version="1.0.0"
)

class Item(BaseModel):
    name: str
    price: float

@router.get("/")
def root():
    return {"message": "Hello from Django!"}

@router.get("/items/{item_id}")
def get_item(item_id: int):
    return {"item_id": item_id}

@router.post("/items", response_model=Item, status_code=201)
def create_item(item: Item):
    return item

# Django URL configuration
urlpatterns = [
    path("", router.urls)
]

if __name__ == "__main__":
    call_command("runserver", "8000")
```

### Step 3: Run

```bash
python main.py
```

---

## AIOHTTP Example

### Step 1: Install

```bash
pip install fastopenapi[aiohttp]
```

### Step 2: Create `main.py`

```python
from aiohttp import web
from pydantic import BaseModel
from fastopenapi.routers import AioHttpRouter

# Create AIOHTTP app
app = web.Application()

# Create FastOpenAPI router
router = AioHttpRouter(
    app=app,
    title="My AIOHTTP API",
    version="1.0.0"
)

class Item(BaseModel):
    name: str
    price: float

@router.get("/")
async def root():
    return {"message": "Hello from AIOHTTP!"}

@router.get("/items/{item_id}")
async def get_item(item_id: int):
    return {"item_id": item_id}

@router.post("/items", response_model=Item, status_code=201)
async def create_item(item: Item):
    return item

if __name__ == "__main__":
    web.run_app(app, host="127.0.0.1", port=8000)
```

### Step 3: Run

```bash
python main.py
```

---

## Falcon Example

### Step 1: Install

```bash
pip install fastopenapi[falcon] uvicorn
```

### Step 2: Create `main.py`

```python
import falcon.asgi
import uvicorn
from pydantic import BaseModel
from fastopenapi.routers import FalconAsyncRouter

# Create Falcon app
app = falcon.asgi.App()

# Create FastOpenAPI router
router = FalconAsyncRouter(
    app=app,
    title="My Falcon API",
    version="1.0.0"
)

class Item(BaseModel):
    name: str
    price: float

@router.get("/")
async def root():
    return {"message": "Hello from Falcon!"}

@router.get("/items/{item_id}")
async def get_item(item_id: int):
    return {"item_id": item_id}

@router.post("/items", response_model=Item, status_code=201)
async def create_item(item: Item):
    return item

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

### Step 3: Run

```bash
python main.py
```

---

## Quart Example

### Step 1: Install

```bash
pip install fastopenapi[quart]
```

### Step 2: Create `main.py`

```python
from quart import Quart
from pydantic import BaseModel
from fastopenapi.routers import QuartRouter

# Create Quart app
app = Quart(__name__)

# Create FastOpenAPI router
router = QuartRouter(
    app=app,
    title="My Quart API",
    version="1.0.0"
)

class Item(BaseModel):
    name: str
    price: float

@router.get("/")
async def root():
    return {"message": "Hello from Quart!"}

@router.get("/items/{item_id}")
async def get_item(item_id: int):
    return {"item_id": item_id}

@router.post("/items", response_model=Item, status_code=201)
async def create_item(item: Item):
    return item

if __name__ == "__main__":
    app.run(port=8000)
```

### Step 3: Run

```bash
python main.py
```

---

## Sanic Example

### Step 1: Install

```bash
pip install fastopenapi[sanic]
```

### Step 2: Create `main.py`

```python
from sanic import Sanic
from pydantic import BaseModel
from fastopenapi.routers import SanicRouter

# Create Sanic app
app = Sanic("MyAPI")

# Create FastOpenAPI router
router = SanicRouter(
    app=app,
    title="My Sanic API",
    version="1.0.0"
)

class Item(BaseModel):
    name: str
    price: float

@router.get("/")
async def root():
    return {"message": "Hello from Sanic!"}

@router.get("/items/{item_id}")
async def get_item(item_id: int):
    return {"item_id": item_id}

@router.post("/items", response_model=Item, status_code=201)
async def create_item(item: Item):
    return item

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

### Step 3: Run

```bash
python main.py
```

---

## Tornado Example

### Step 1: Install

```bash
pip install fastopenapi[tornado]
```

### Step 2: Create `main.py`

```python
import asyncio
from tornado.web import Application
from pydantic import BaseModel
from fastopenapi.routers import TornadoRouter

# Create Tornado app
app = Application()

# Create FastOpenAPI router
router = TornadoRouter(
    app=app,
    title="My Tornado API",
    version="1.0.0"
)

class Item(BaseModel):
    name: str
    price: float

@router.get("/")
async def root():
    return {"message": "Hello from Tornado!"}

@router.get("/items/{item_id}")
async def get_item(item_id: int):
    return {"item_id": item_id}

@router.post("/items", response_model=Item, status_code=201)
async def create_item(item: Item):
    return item

async def main():
    app.listen(8000)
    print("Server started on http://localhost:8000")
    print("Documentation at http://localhost:8000/docs")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 3: Run

```bash
python main.py
```

---

## Testing Your API

Once your server is running, you can test your API in several ways:

### Using a Browser

Visit the documentation pages:

- **Swagger UI**: `http://localhost:8000/docs` - Interactive API testing
- **ReDoc**: `http://localhost:8000/redoc` - Clean, readable documentation
- **OpenAPI JSON**: `http://localhost:8000/openapi.json` - Raw OpenAPI schema

### Using curl

```bash
# GET request
curl http://localhost:8000/items/1

# POST request
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Item", "price": 9.99}'
```

### Using httpie

```bash
# GET request
http :8000/items/1

# POST request
http POST :8000/items name="Test Item" price:=9.99
```

### Using Python requests

```python
import requests

# GET request
response = requests.get("http://localhost:8000/items/1")
print(response.json())

# POST request
item = {"name": "Test Item", "price": 9.99}
response = requests.post("http://localhost:8000/items", json=item)
print(response.json())
```

## What's Next?

Now that you have a working API, explore more features:

- [Core Concepts](core_concepts.md) - Understand how FastOpenAPI works
- [Routing](../guide/routing.md) - Learn about HTTP methods and path parameters
- [Request Parameters](../guide/request_parameters.md) - Query, path, and header parameters
- [Request Body](../guide/request_body.md) - Handle JSON, forms, and file uploads
- [Validation](../guide/validation.md) - Use Pydantic for robust validation
- [Framework Guides](../frameworks/overview.md) - Framework-specific details

## Troubleshooting

### Port Already in Use

If you get an error that port 8000 is already in use, change the port:

```python
# For Flask
app.run(port=8001)

# For Uvicorn-based frameworks
uvicorn.run(app, port=8001)

# For Tornado
app.listen(8001)
```

### Import Errors

If you get an import error, make sure you installed the framework extra:

```bash
pip install fastopenapi[your-framework]
```

### Module Not Found

If Python can't find your `main.py`, make sure you're in the correct directory:

```bash
cd /path/to/your/project
python main.py
```
