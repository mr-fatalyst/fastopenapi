# Tornado Integration

Tornado is a Python web framework and asynchronous networking library. This guide covers how to use FastOpenAPI with Tornado.

## Installation

```bash
pip install fastopenapi[tornado]
```

## Basic Setup

```python
import asyncio
from tornado.web import Application
from pydantic import BaseModel
from fastopenapi.routers import TornadoRouter

app = Application()
router = TornadoRouter(
    app=app,
    title="Tornado API",
    version="1.0.0"
)

class Item(BaseModel):
    name: str
    price: float

@router.get("/")
async def root():
    return {"message": "Hello from Tornado!"}

@router.post("/items", response_model=Item, status_code=201)
async def create_item(item: Item):
    return item

async def main():
    app.listen(8000)
    print("Server running on http://localhost:8000")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
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

## Tornado-Specific Features

### Using Tornado Request Handler

```python
from tornado.web import RequestHandler

# You can still use traditional Tornado handlers alongside FastOpenAPI
class CustomHandler(RequestHandler):
    def get(self):
        self.write({"message": "Traditional Tornado handler"})

# Add to app
app.add_handlers(r".*", [(r"/custom", CustomHandler)])
```

### Asynchronous Operations

```python
import asyncio

@router.get("/slow")
async def slow_endpoint():
    # Simulate slow operation
    await asyncio.sleep(2)
    return {"message": "Done"}
```

### Background Tasks

```python
from tornado.ioloop import IOLoop

@router.post("/send-email")
async def send_email(email: str = Form(...)):
    # Schedule background task
    IOLoop.current().spawn_callback(send_email_task, email)
    return {"message": "Email will be sent"}

async def send_email_task(email: str):
    await asyncio.sleep(1)
    print(f"Email sent to {email}")
```

## Database Integration

### Using Motor (MongoDB)

```python
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient('mongodb://localhost:27017')
db = client.test_database

@router.get("/users/{user_id}")
async def get_user(user_id: str):
    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise ResourceNotFoundError(f"User {user_id} not found")
    return user
```

### Using asyncpg (PostgreSQL)

```python
import asyncpg

# Create connection pool at startup
async def create_pool():
    return await asyncpg.create_pool(
        "postgresql://user:password@localhost/db"
    )

@router.get("/users/{user_id}")
async def get_user(user_id: int):
    pool = await create_pool()
    async with pool.acquire() as conn:
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

### Using Tornado Errors

```python
from tornado.web import HTTPError

@router.get("/items/{item_id}")
async def get_item(item_id: int):
    item = await database.get(item_id)
    if not item:
        raise HTTPError(status_code=404, reason="Item not found")
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
    return {"user_id": user_id}
```

## WebSocket Support

```python
from tornado.websocket import WebSocketHandler

class ChatWebSocket(WebSocketHandler):
    def open(self):
        print("WebSocket opened")
    
    def on_message(self, message):
        self.write_message(f"Echo: {message}")
    
    def on_close(self):
        print("WebSocket closed")

# Add WebSocket handler
app.add_handlers(r".*", [(r"/ws", ChatWebSocket)])
```

## Testing

```python
import pytest
from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application

class TestAPI(AsyncHTTPTestCase):
    def get_app(self):
        return app
    
    def test_root(self):
        response = self.fetch('/')
        self.assertEqual(response.code, 200)
        data = json.loads(response.body)
        self.assertEqual(data["message"], "Hello from Tornado!")
    
    def test_create_item(self):
        response = self.fetch(
            '/items',
            method='POST',
            body=json.dumps({"name": "Test", "price": 9.99}),
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(response.code, 201)
```

## Complete Example

```python
import asyncio
from tornado.web import Application
from pydantic import BaseModel, EmailStr
from fastopenapi.routers import TornadoRouter
from fastopenapi.errors import ResourceNotFoundError
from fastopenapi import Query

app = Application()
router = TornadoRouter(
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

async def main():
    app.listen(8000)
    print("Server running on http://localhost:8000")
    print("Docs at http://localhost:8000/docs")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
```

## Deployment

### Development

```bash
python main.py
```

### Production

For production, use multiple processes:

```python
import tornado.httpserver
import tornado.ioloop

if __name__ == "__main__":
    server = tornado.httpserver.HTTPServer(app)
    server.bind(8000)
    server.start(4)  # 4 processes
    tornado.ioloop.IOLoop.current().start()
```

Or use supervisor/systemd to manage processes.

## Configuration

### Settings

```python
from tornado.options import define, options

define("port", default=8000, help="run on the given port", type=int)
define("debug", default=False, help="run in debug mode", type=bool)

async def main():
    tornado.options.parse_command_line()
    app.listen(options.port)
    print(f"Server running on port {options.port}")
    await asyncio.Event().wait()
```

Run with:
```bash
python main.py --port=8080 --debug=true
```

## Periodic Tasks

```python
from tornado.ioloop import PeriodicCallback

def periodic_task():
    print("Running periodic task")

# Run every 60 seconds
PeriodicCallback(periodic_task, 60000).start()
```

## Static Files

```python
import os

app = Application(
    router.routes,
    static_path=os.path.join(os.path.dirname(__file__), "static"),
    static_url_prefix="/static/"
)
```

## Templates

```python
import os

app = Application(
    router.routes,
    template_path=os.path.join(os.path.dirname(__file__), "templates")
)

from tornado.web import RequestHandler

class TemplateHandler(RequestHandler):
    def get(self):
        self.render("index.html", title="My App")

app.add_handlers(r".*", [(r"/", TemplateHandler)])
```

## Security

### XSRF Protection

```python
app = Application(
    router.routes,
    cookie_secret="your-secret-key",
    xsrf_cookies=True
)
```

### Secure Cookies

```python
from tornado.web import RequestHandler

class SecureHandler(RequestHandler):
    def get(self):
        self.set_secure_cookie("user", "username")
        self.write("Cookie set")
    
    def post(self):
        user = self.get_secure_cookie("user")
        self.write(f"User: {user}")
```

## Next Steps

- [Core Concepts](../getting_started/core_concepts.md)
- [Async Patterns](../examples/async_tasks.md)
- [Performance](../advanced/performance.md)
