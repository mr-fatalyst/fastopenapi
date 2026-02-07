# Quart Integration

Quart is an async Python web framework with a Flask-compatible API. This guide shows how to use FastOpenAPI with Quart.

## Installation

```bash
pip install fastopenapi[quart]
```

## Basic Setup

```python
from quart import Quart
from pydantic import BaseModel
from fastopenapi.routers import QuartRouter

app = Quart(__name__)
router = QuartRouter(
    app=app,
    title="Quart API",
    version="1.0.0"
)

class Item(BaseModel):
    name: str
    price: float

@router.get("/")
async def root():
    return {"message": "Hello from Quart!"}

@router.post("/items", response_model=Item, status_code=201)
async def create_item(item: Item):
    return item

if __name__ == "__main__":
    app.run(port=8000)
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

## Quart-Specific Features

### Using Quart Request

```python
from quart import request

@router.get("/request-info")
async def get_request_info():
    return {
        "method": request.method,
        "path": request.path,
        "remote_addr": request.remote_addr,
        "user_agent": request.user_agent.string
    }
```

### Using Quart Response

```python
from quart import Response

@router.get("/custom-response")
async def custom_response():
    return Response('{"message": "custom"}', mimetype="application/json")
```

### Sessions

```python
from quart import session

app.secret_key = "your-secret-key"

@router.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    if authenticate(username, password):
        session["user_id"] = get_user_id(username)
        return {"message": "Logged in"}
    raise AuthenticationError("Invalid credentials")

@router.get("/profile")
async def profile():
    user_id = session.get("user_id")
    if not user_id:
        raise AuthenticationError("Not logged in")
    return {"user_id": user_id}
```

### Blueprints

```python
from quart import Blueprint

# Create blueprint
api_bp = Blueprint("api", __name__, url_prefix="/api")

# Create router for blueprint
api_router = QuartRouter(app=api_bp)

@api_router.get("/items")
async def list_items():
    return {"items": []}

# Register blueprint
app.register_blueprint(api_bp)
```

### WebSocket Support

```python
from quart import websocket

@app.websocket('/ws')
async def ws():
    while True:
        data = await websocket.receive()
        await websocket.send(f"Echo: {data}")
```

## Database Integration

### Using asyncpg (PostgreSQL)

```python
import asyncpg

async def get_db_pool():
    return await asyncpg.create_pool(
        "postgresql://user:password@localhost/db"
    )

@router.get("/users/{user_id}")
async def get_user(user_id: int):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT * FROM users WHERE id = $1", user_id
        )
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found")
        return dict(user)
```

### Using SQLAlchemy (Async)

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastopenapi import Depends

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")
async_session = sessionmaker(engine, class_=AsyncSession)

async def get_db():
    async with async_session() as session:
        yield session

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

### Using Quart Errors

```python
from quart import abort

@router.get("/items/{item_id}")
async def get_item(item_id: int):
    item = await database.get(item_id)
    if not item:
        abort(404, description="Item not found")
    return item
```

## Authentication

### JWT Authentication

```python
import jwt
from datetime import datetime, timedelta
from fastopenapi import Security, Depends, Header
from fastopenapi.errors import AuthenticationError

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_bearer_token(authorization: str = Header(..., alias="Authorization")):
    if not authorization.startswith("Bearer "):
        raise AuthenticationError("Invalid authorization header")
    return authorization[7:]

def verify_token(token: str = Depends(get_bearer_token)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["user_id"]
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token")

@router.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    user = authenticate_user(username, password)
    if not user:
        raise AuthenticationError("Invalid credentials")

    access_token = create_access_token(data={"user_id": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/protected")
async def protected(user_id: str = Security(verify_token)):
    return {"user_id": user_id, "message": "Access granted"}
```

## Background Tasks

```python
import asyncio

@router.post("/send-email")
async def send_email(email: str = Form(...)):
    # Start background task
    asyncio.create_task(send_email_task(email))
    return {"message": "Email will be sent"}

async def send_email_task(email: str):
    await asyncio.sleep(1)  # Simulate sending
    print(f"Email sent to {email}")
```

## CORS

Use Quart-CORS:

```bash
pip install quart-cors
```

```python
from quart_cors import cors

app = Quart(__name__)
app = cors(app, allow_origin="*")

router = QuartRouter(app=app)
```

## Testing

```python
import pytest

@pytest.fixture
def app():
    app = Quart(__name__)
    router = QuartRouter(app=app)
    
    @router.get("/")
    async def root():
        return {"message": "test"}
    
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.mark.asyncio
async def test_root(client):
    response = await client.get('/')
    assert response.status_code == 200
    data = await response.get_json()
    assert data["message"] == "test"

@pytest.mark.asyncio
async def test_create_item(client):
    response = await client.post(
        '/items',
        json={"name": "Test", "price": 9.99}
    )
    assert response.status_code == 201
```

## Complete Example

```python
from quart import Quart
from pydantic import BaseModel, EmailStr
from fastopenapi.routers import QuartRouter
from fastopenapi.errors import ResourceNotFoundError
from fastopenapi import Query

app = Quart(__name__)
router = QuartRouter(
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
    app.run(port=8000)
```

## Deployment

### Development

```bash
python main.py
```

Or use hypercorn:

```bash
pip install hypercorn
hypercorn main:app --reload
```

### Production

```bash
hypercorn main:app --bind 0.0.0.0:8000 --workers 4
```

## Migrating from Flask

Quart is designed to be Flask-compatible:

```python
# Flask code
from flask import Flask

# Just change to Quart
from quart import Quart

# Add async to route handlers
@router.get("/")
async def root():  # Add async here
    return {"message": "Hello"}
```

## Next Steps

- [Core Concepts](../getting_started/core_concepts.md) - Understand FastOpenAPI
- [Async Patterns](../examples/async_tasks.md) - Learn async patterns
- [Dependencies](../guide/dependencies.md) - Use dependency injection
