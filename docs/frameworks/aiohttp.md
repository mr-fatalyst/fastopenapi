# AIOHTTP Integration

AIOHTTP is a popular asynchronous HTTP client/server framework. This guide covers how to use FastOpenAPI with AIOHTTP.

## Installation

```bash
pip install fastopenapi[aiohttp]
```

## Basic Setup

```python
from aiohttp import web
from pydantic import BaseModel
from fastopenapi.routers import AioHttpRouter

app = web.Application()
router = AioHttpRouter(
    app=app,
    title="AIOHTTP API",
    version="1.0.0"
)

class Item(BaseModel):
    name: str
    price: float

@router.get("/")
async def root():
    return {"message": "Hello from AIOHTTP!"}

@router.post("/items", response_model=Item, status_code=201)
async def create_item(item: Item):
    return item

if __name__ == "__main__":
    web.run_app(app, host="127.0.0.1", port=8000)
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
class UserCreate(BaseModel):
    username: str
    email: str
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
    # Authenticate
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
        "size": len(content),
        "content_type": file.content_type
    }
```

## Working with AIOHTTP Features

### Accessing Request Object

```python
from aiohttp import web

@router.get("/request-info")
async def get_request_info():
    # Can access aiohttp.web.Request if needed
    return {"message": "Request info"}
```

### Using AIOHTTP Response

```python
from aiohttp import web

@router.get("/custom-response")
async def custom_response():
    # Return aiohttp response directly
    return web.Response(
        text='{"message": "Custom"}',
        content_type="application/json"
    )
```

### Middleware

```python
@web.middleware
async def timing_middleware(request, handler):
    import time
    start = time.time()
    response = await handler(request)
    elapsed = time.time() - start
    response.headers['X-Response-Time'] = str(elapsed)
    return response

app = web.Application(middlewares=[timing_middleware])
router = AioHttpRouter(app=app)
```

### Background Tasks

```python
import asyncio

@router.post("/send-email")
async def send_email(email: str = Form(...)):
    # Start background task
    asyncio.create_task(send_email_async(email))
    return {"message": "Email will be sent"}

async def send_email_async(email: str):
    await asyncio.sleep(1)  # Simulate email sending
    print(f"Email sent to {email}")
```

## Database Integration

### Using aiopg (PostgreSQL)

```python
import aiopg

async def get_db_pool():
    return await aiopg.create_pool(
        "dbname=test user=postgres password=secret"
    )

@router.get("/users/{user_id}")
async def get_user(user_id: int):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = await cur.fetchone()
            if not user:
                raise ResourceNotFoundError(f"User {user_id} not found")
            return {"id": user[0], "name": user[1]}
```

### Using Motor (MongoDB)

```python
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient('mongodb://localhost:27017')
db = client.test_database

@router.get("/items/{item_id}")
async def get_item(item_id: str):
    item = await db.items.find_one({"_id": item_id})
    if not item:
        raise ResourceNotFoundError(f"Item {item_id} not found")
    return item
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

### Using AIOHTTP Errors

```python
from aiohttp import web

@router.get("/items/{item_id}")
async def get_item(item_id: int):
    item = await database.get(item_id)
    if not item:
        raise web.HTTPNotFound(reason="Item not found")
    return item
```

## Authentication

### JWT Authentication

```python
import jwt
from fastopenapi import Security, Depends, Header
from fastopenapi.errors import AuthenticationError

SECRET_KEY = "your-secret-key"

def get_bearer_token(authorization: str = Header(..., alias="Authorization")):
    if not authorization.startswith("Bearer "):
        raise AuthenticationError("Invalid authorization header")
    return authorization[7:]

def verify_token(token: str = Depends(get_bearer_token)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["user_id"]
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token")

@router.get("/protected")
async def protected(user_id: str = Security(verify_token)):
    return {"user_id": user_id, "message": "Access granted"}
```

## WebSocket Support

AIOHTTP has built-in WebSocket support:

```python
from aiohttp import web

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    async for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            await ws.send_str(f"Echo: {msg.data}")
        elif msg.type == web.WSMsgType.ERROR:
            print(f'Connection closed with exception {ws.exception()}')
    
    return ws

app.router.add_route('GET', '/ws', websocket_handler)
```

## Testing

```python
from aiohttp.test_utils import AioHTTPTestCase
from aiohttp import web

class TestAPI(AioHTTPTestCase):
    async def get_application(self):
        return app
    
    async def test_root(self):
        async with self.client.request("GET", "/") as resp:
            self.assertEqual(resp.status, 200)
            data = await resp.json()
            self.assertEqual(data["message"], "Hello from AIOHTTP!")
    
    async def test_create_item(self):
        async with self.client.request(
            "POST", 
            "/items",
            json={"name": "Test", "price": 9.99}
        ) as resp:
            self.assertEqual(resp.status, 201)
            data = await resp.json()
            self.assertEqual(data["name"], "Test")
```

## Complete Example

```python
from aiohttp import web
from pydantic import BaseModel, EmailStr
from fastopenapi.routers import AioHttpRouter
from fastopenapi.errors import ResourceNotFoundError
from fastopenapi import Query
import asyncio

app = web.Application()
router = AioHttpRouter(
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
    web.run_app(app, host="127.0.0.1", port=8000)
```

## Deployment

### Development

```bash
python main.py
```

### Production with Gunicorn

```bash
pip install gunicorn aiohttp-gunicorn

gunicorn main:app --bind 0.0.0.0:8000 --worker-class aiohttp.GunicornWebWorker --workers 4
```

## Next Steps

- [Core Concepts](../getting_started/core_concepts.md) - Understand FastOpenAPI
- [Async Patterns](../examples/async_tasks.md) - Learn async patterns
- [Dependencies](../guide/dependencies.md) - Use dependency injection
