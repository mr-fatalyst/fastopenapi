# Sanic Integration

Sanic is a fast Python async web framework built for speed. This guide covers how to use FastOpenAPI with Sanic.

## Installation

```bash
pip install fastopenapi[sanic]
```

## Basic Setup

```python
from sanic import Sanic
from pydantic import BaseModel
from fastopenapi.routers import SanicRouter

app = Sanic("MyAPI")
router = SanicRouter(
    app=app,
    title="Sanic API",
    version="1.0.0"
)

class Item(BaseModel):
    name: str
    price: float

@router.get("/")
async def root():
    return {"message": "Hello from Sanic!"}

@router.post("/items", response_model=Item, status_code=201)
async def create_item(item: Item):
    return item

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

## Path Parameters

```python
from fastopenapi import Path

@router.get("/users/{user_id}")
async def get_user(user_id: int = Path(..., description="User ID")):
    return {"user_id": user_id}
```

## Request Data

### Query Parameters

```python
from fastopenapi import Query

@router.get("/search")
async def search(
    q: str = Query(..., description="Search query"),
    page: int = Query(1, ge=1)
):
    return {"query": q, "page": page}
```

### Request Body

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

### Form Data

```python
from fastopenapi import Form

@router.post("/login")
async def login(
    username: str = Form(...),
    password: str = Form(...)
):
    return {"username": username}
```

### File Upload

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

## Sanic-Specific Features

### Using Sanic Request

```python
from sanic import request

@router.get("/request-info")
async def get_request_info():
    return {
        "ip": request.ip,
        "host": request.host,
        "scheme": request.scheme
    }
```

### Using Sanic Response

```python
from sanic import response

@router.get("/custom-response")
async def custom_response():
    return response.json({"message": "custom"})
```

### Background Tasks

```python
from sanic import Sanic

@router.post("/send-email")
async def send_email(email: str = Form(...)):
    # Add background task
    app.add_task(send_email_task(email))
    return {"message": "Email will be sent"}

async def send_email_task(email: str):
    await asyncio.sleep(1)
    print(f"Email sent to {email}")
```

### Middleware

```python
@app.middleware('request')
async def add_request_id(request):
    request.ctx.request_id = str(uuid.uuid4())

@app.middleware('response')
async def add_response_header(request, response):
    response.headers["X-Request-ID"] = request.ctx.request_id
```

### Listeners

```python
@app.before_server_start
async def setup_db(app, loop):
    app.ctx.db = await create_db_pool()

@app.after_server_stop
async def cleanup_db(app, loop):
    await app.ctx.db.close()
```

## Database Integration

### Using asyncpg

```python
import asyncpg

@app.before_server_start
async def create_db_pool(app, loop):
    app.ctx.db = await asyncpg.create_pool(
        "postgresql://user:password@localhost/db"
    )

@router.get("/users/{user_id}")
async def get_user(user_id: int):
    async with app.ctx.db.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT * FROM users WHERE id = $1", user_id
        )
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found")
        return dict(user)
```

## Error Handling

### Using FastOpenAPI Errors

```python
from fastopenapi.errors import (
    BadRequestError,
    ResourceNotFoundError
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

### Using Sanic Errors

```python
from sanic.exceptions import NotFound, ServerError

@router.get("/items/{item_id}")
async def get_item(item_id: int):
    item = await database.get(item_id)
    if not item:
        raise NotFound("Item not found")
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

## WebSocket Support

```python
@app.websocket("/ws")
async def websocket_handler(request, ws):
    while True:
        data = await ws.recv()
        await ws.send(f"Echo: {data}")
```

## Testing

```python
import pytest

@pytest.fixture
def app():
    app = Sanic("test")
    router = SanicRouter(app=app)
    
    @router.get("/")
    async def root():
        return {"message": "test"}
    
    return app

def test_root(app):
    _, response = app.test_client.get('/')
    assert response.status == 200
    assert response.json["message"] == "test"

def test_create_item(app):
    _, response = app.test_client.post(
        '/items',
        json={"name": "Test", "price": 9.99}
    )
    assert response.status == 201
```

## Complete Example

```python
from sanic import Sanic
from pydantic import BaseModel, EmailStr
from fastopenapi.routers import SanicRouter
from fastopenapi.errors import ResourceNotFoundError
from fastopenapi import Query

app = Sanic("UserAPI")
router = SanicRouter(
    app=app,
    title="User Management API",
    version="1.0.0"
)

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
    app.run(host="0.0.0.0", port=8000, debug=True)
```

## Deployment

### Development

```bash
python main.py
```

### Production

```bash
sanic main.app --host=0.0.0.0 --port=8000 --workers=4
```

Or with environment variables:

```bash
export SANIC_HOST=0.0.0.0
export SANIC_PORT=8000
export SANIC_WORKERS=4
sanic main.app
```

## Performance

Sanic is built for speed. Tips:

1. **Use workers** - `--workers=N` for CPU-bound tasks
2. **Enable fast** mode - `--fast` for production
3. **Use connection pooling** for databases
4. **Profile with** `sanic-testing`
5. **Monitor with** built-in statistics

## Next Steps

- [Core Concepts](../getting_started/core_concepts.md)
- [Async Patterns](../examples/async_tasks.md)
- [Performance](../advanced/performance.md)
