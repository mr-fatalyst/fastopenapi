# Falcon Integration

Falcon is a minimalist Python web framework for building fast APIs. This guide covers how to use FastOpenAPI with both Falcon WSGI (synchronous) and ASGI (asynchronous) modes.

## Installation

```bash
pip install fastopenapi[falcon]
```

## Basic Setup

FastOpenAPI provides two routers for Falcon:
- `FalconRouter` - for synchronous WSGI apps
- `FalconAsyncRouter` - for asynchronous ASGI apps

### Synchronous Falcon (WSGI)

```python
import falcon
from pydantic import BaseModel
from fastopenapi.routers import FalconRouter

app = falcon.App()
router = FalconRouter(
    app=app,
    title="Falcon API",
    version="1.0.0"
)

class Item(BaseModel):
    name: str
    price: float

@router.get("/")
def root():
    return {"message": "Hello from Falcon!"}

@router.post("/items", response_model=Item, status_code=201)
def create_item(item: Item):
    return item

if __name__ == "__main__":
    from wsgiref import simple_server
    httpd = simple_server.make_server('127.0.0.1', 8000, app)
    httpd.serve_forever()
```

### Asynchronous Falcon (ASGI)

```python
import falcon.asgi
import uvicorn
from pydantic import BaseModel
from fastopenapi.routers import FalconAsyncRouter

app = falcon.asgi.App()
router = FalconAsyncRouter(
    app=app,
    title="Falcon Async API",
    version="1.0.0"
)

class Item(BaseModel):
    name: str
    price: float

@router.get("/")
async def root():
    return {"message": "Hello from async Falcon!"}

@router.post("/items", response_model=Item, status_code=201)
async def create_item(item: Item):
    return item

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

## Path Parameters

=== "Async (ASGI)"

    ```python
    from fastopenapi import Path

    @router.get("/users/{user_id}")
    async def get_user(user_id: int = Path(..., description="User ID")):
        return {"user_id": user_id}
    ```

=== "Sync (WSGI)"

    ```python
    from fastopenapi import Path

    @router.get("/users/{user_id}")
    def get_user(user_id: int = Path(..., description="User ID")):
        return {"user_id": user_id}
    ```

## Request Data

### Query Parameters

=== "Async (ASGI)"

    ```python
    from fastopenapi import Query

    @router.get("/search")
    async def search(
        q: str = Query(..., description="Search query"),
        page: int = Query(1, ge=1)
    ):
        return {"query": q, "page": page}
    ```

=== "Sync (WSGI)"

    ```python
    from fastopenapi import Query

    @router.get("/search")
    def search(
        q: str = Query(..., description="Search query"),
        page: int = Query(1, ge=1)
    ):
        return {"query": q, "page": page}
    ```

### Request Body

=== "Async (ASGI)"

    ```python
    from pydantic import BaseModel, EmailStr

    class UserCreate(BaseModel):
        username: str
        email: EmailStr
        age: int

    @router.post("/users", status_code=201)
    async def create_user(user: UserCreate):
        return {"username": user.username, "email": user.email}
    ```

=== "Sync (WSGI)"

    ```python
    from pydantic import BaseModel, EmailStr

    class UserCreate(BaseModel):
        username: str
        email: EmailStr
        age: int

    @router.post("/users", status_code=201)
    def create_user(user: UserCreate):
        return {"username": user.username, "email": user.email}
    ```

### Form Data

=== "Async (ASGI)"

    ```python
    from fastopenapi import Form

    @router.post("/login")
    async def login(
        username: str = Form(...),
        password: str = Form(...)
    ):
        return {"username": username}
    ```

=== "Sync (WSGI)"

    ```python
    from fastopenapi import Form

    @router.post("/login")
    def login(
        username: str = Form(...),
        password: str = Form(...)
    ):
        return {"username": username}
    ```

### File Upload

=== "Async (ASGI)"

    ```python
    from fastopenapi import File, FileUpload

    @router.post("/upload")
    async def upload_file(file: FileUpload = File(...)):
        content = await file.aread()
        return {
            "filename": file.filename,
            "size": len(content)
        }
    ```

=== "Sync (WSGI)"

    ```python
    from fastopenapi import File, FileUpload

    @router.post("/upload")
    def upload_file(file: FileUpload = File(...)):
        content = file.read()
        return {
            "filename": file.filename,
            "size": len(content)
        }
    ```

## Falcon-Specific Features

### Using Falcon Request/Response

```python
import falcon

@router.get("/falcon-response")
async def falcon_response():
    # Can return Falcon Response directly
    resp = falcon.Response()
    resp.media = {"message": "Falcon response"}
    resp.set_header("X-Custom", "Value")
    return resp
```

### Falcon Hooks

```python
def validate_api_key(req, resp, resource, params):
    """Hook to validate API key"""
    api_key = req.get_header('X-API-Key')
    if api_key != 'secret':
        raise falcon.HTTPUnauthorized('Unauthorized', 'Invalid API key')

# Apply hook to specific endpoint
@router.get("/protected")
@falcon.before(validate_api_key)
async def protected():
    return {"message": "Access granted"}
```

### Falcon Middleware

```python
class AuthMiddleware:
    async def process_request(self, req, resp):
        # Process request before handler
        token = req.get_header('Authorization')
        if not token:
            raise falcon.HTTPUnauthorized()
    
    async def process_response(self, req, resp, resource, req_succeeded):
        # Process response after handler
        resp.set_header('X-Powered-By', 'Falcon')

app = falcon.asgi.App(middleware=[AuthMiddleware()])
router = FalconAsyncRouter(app=app)
```

## Database Integration

### Using SQLAlchemy (Async)

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with async_session() as session:
        yield session

from fastopenapi import Depends

@router.get("/users/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise ResourceNotFoundError(f"User {user_id} not found")
    return {"id": user.id, "username": user.username}
```

## Error Handling

### Using FastOpenAPI Errors

```python
from fastopenapi.errors import (
    BadRequestError,
    ResourceNotFoundError,
    AuthenticationError
)

@router.get("/items/{item_id}")
async def get_item(item_id: int):
    if item_id < 0:
        raise BadRequestError("Item ID must be positive")
    
    item = await database.get(item_id)
    if not item:
        raise ResourceNotFoundError(f"Item {item_id} not found")
    
    return item
```

### Using Falcon Errors

```python
import falcon

@router.get("/items/{item_id}")
async def get_item(item_id: int):
    item = await database.get(item_id)
    if not item:
        raise falcon.HTTPNotFound(
            title="Not Found",
            description=f"Item {item_id} not found"
        )
    return item
```

## Authentication

### JWT Authentication

```python
import jwt
from fastopenapi import Security, Depends
from fastopenapi.errors import AuthenticationError

SECRET_KEY = "your-secret-key"

def verify_token(token: str = Security()):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["user_id"]
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token")

@router.get("/protected")
async def protected(user_id: str = Depends(verify_token)):
    return {"user_id": user_id}
```

## Testing

### Async Testing

```python
import pytest
from falcon import testing

@pytest.fixture
def client():
    return testing.TestClient(app)

def test_root(client):
    response = client.simulate_get('/')
    assert response.status_code == 200
    assert response.json == {"message": "Hello from async Falcon!"}

def test_create_item(client):
    response = client.simulate_post(
        '/items',
        json={"name": "Test", "price": 9.99}
    )
    assert response.status_code == 201
    assert response.json["name"] == "Test"
```

## Complete Example

```python
import falcon.asgi
import uvicorn
from pydantic import BaseModel, EmailStr
from fastopenapi.routers import FalconAsyncRouter
from fastopenapi.errors import ResourceNotFoundError
from fastopenapi import Query

app = falcon.asgi.App()
router = FalconAsyncRouter(
    app=app,
    title="User Management API",
    version="1.0.0"
)

# In-memory database
users_db = {}
next_id = 1

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

class UserCreate(BaseModel):
    username: str
    email: EmailStr

@router.get("/", tags=["Root"])
async def root():
    return {"message": "User Management API"}

@router.get("/users", response_model=list[UserResponse], tags=["Users"])
async def list_users(limit: int = Query(10, ge=1, le=100)):
    users = list(users_db.values())[:limit]
    return users

@router.get("/users/{user_id}", response_model=UserResponse, tags=["Users"])
async def get_user(user_id: int):
    user = users_db.get(user_id)
    if not user:
        raise ResourceNotFoundError(f"User {user_id} not found")
    return user

@router.post("/users", response_model=UserResponse, status_code=201, tags=["Users"])
async def create_user(user: UserCreate):
    global next_id
    new_user = {
        "id": next_id,
        "username": user.username,
        "email": user.email
    }
    users_db[next_id] = new_user
    next_id += 1
    return new_user

@router.delete("/users/{user_id}", status_code=204, tags=["Users"])
async def delete_user(user_id: int):
    if user_id not in users_db:
        raise ResourceNotFoundError(f"User {user_id} not found")
    del users_db[user_id]
    return None

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

## Deployment

### Development (Async)

```bash
uvicorn main:app --reload
```

### Development (Sync)

```bash
python main.py
```

### Production (Async)

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Production (Sync)

```bash
gunicorn --bind 0.0.0.0:8000 --workers 4 main:app
```

## Performance Tips

Falcon is designed for performance:

1. **Use ASGI** for async operations
2. **Minimize middleware** - only use what you need
3. **Use connection pooling** for databases
4. **Cache responses** where appropriate
5. **Profile with cProfile** to find bottlenecks

## Next Steps

- [Core Concepts](../getting_started/core_concepts.md) - Understand FastOpenAPI
- [Performance](../advanced/performance.md) - Optimization tips
- [Dependencies](../guide/dependencies.md) - Use dependency injection
