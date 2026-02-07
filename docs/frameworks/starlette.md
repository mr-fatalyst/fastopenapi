# Starlette Integration

Starlette is a lightweight ASGI framework that FastAPI is built upon. This guide covers how to use FastOpenAPI with Starlette.

## Installation

```bash
pip install fastopenapi[starlette]
```

## Basic Setup

```python
import uvicorn
from starlette.applications import Starlette
from pydantic import BaseModel
from fastopenapi.routers import StarletteRouter

app = Starlette()
router = StarletteRouter(
    app=app,
    title="Starlette API",
    version="1.0.0"
)

class Item(BaseModel):
    name: str
    price: float

@router.get("/")
async def root():
    return {"message": "Hello from Starlette!"}

@router.post("/items", response_model=Item, status_code=201)
async def create_item(item: Item):
    return item

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
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

## Starlette-Specific Features

### Using Starlette Request

```python
from starlette.requests import Request

@router.get("/request-info")
async def get_request_info(request: Request):
    return {
        "method": request.method,
        "url": str(request.url),
        "client": request.client.host
    }
```

### Using Starlette Response

```python
from starlette.responses import JSONResponse, PlainTextResponse

@router.get("/json-response")
async def json_response():
    return JSONResponse({"message": "custom"})

@router.get("/text-response")
async def text_response():
    return PlainTextResponse("Hello, World!")
```

### Streaming Response

```python
from starlette.responses import StreamingResponse
import asyncio

@router.get("/stream")
async def stream():
    async def generate():
        for i in range(10):
            yield f"data: {i}\n\n"
            await asyncio.sleep(1)
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

### File Response

```python
from starlette.responses import FileResponse

@router.get("/download/{filename}")
async def download_file(filename: str):
    return FileResponse(
        path=f"/files/{filename}",
        filename=filename,
        media_type="application/octet-stream"
    )
```

### Middleware

```python
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_methods=['*'],
        allow_headers=['*']
    ),
    Middleware(
        TrustedHostMiddleware,
        allowed_hosts=['example.com', '*.example.com']
    )
]

app = Starlette(middleware=middleware)
router = StarletteRouter(app=app)
```

### Background Tasks

```python
from starlette.background import BackgroundTask

@router.post("/send-email")
async def send_email(email: str = Form(...)):
    task = BackgroundTask(send_email_task, email)
    return JSONResponse(
        {"message": "Email will be sent"},
        background=task
    )

async def send_email_task(email: str):
    await asyncio.sleep(1)
    print(f"Email sent to {email}")
```

### Lifespan Events

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    # Startup
    print("Starting up...")
    app.state.db = await create_db_pool()
    yield
    # Shutdown
    print("Shutting down...")
    await app.state.db.close()

app = Starlette(lifespan=lifespan)
router = StarletteRouter(app=app)
```

## Database Integration

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
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise ResourceNotFoundError(f"User {user_id} not found")
    return {"id": user.id, "username": user.username}
```

### Using Databases Library

```python
import databases

database = databases.Database("postgresql://user:pass@localhost/db")

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@router.get("/users/{user_id}")
async def get_user(user_id: int):
    query = "SELECT * FROM users WHERE id = :user_id"
    user = await database.fetch_one(query, values={"user_id": user_id})
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

### Using Starlette Errors

```python
from starlette.exceptions import HTTPException

@router.get("/items/{item_id}")
async def get_item(item_id: int):
    item = await database.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
```

### Custom Error Handler

```python
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

async def http_exception_handler(request, exc):
    return JSONResponse(
        {
            "error": {
                "message": exc.detail,
                "status": exc.status_code
            }
        },
        status_code=exc.status_code
    )

app.add_exception_handler(HTTPException, http_exception_handler)
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

## WebSocket Support

```python
from starlette.websockets import WebSocket

@app.websocket_route('/ws')
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")
```

## Testing

```python
from starlette.testclient import TestClient

def test_root():
    client = TestClient(app)
    response = client.get('/')
    assert response.status_code == 200
    assert response.json()["message"] == "Hello from Starlette!"

def test_create_item():
    client = TestClient(app)
    response = client.post(
        '/items',
        json={"name": "Test", "price": 9.99}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test"
```

## Complete Example

```python
import uvicorn
from starlette.applications import Starlette
from pydantic import BaseModel, EmailStr
from fastopenapi.routers import StarletteRouter
from fastopenapi.errors import ResourceNotFoundError
from fastopenapi import Query

app = Starlette()
router = StarletteRouter(
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
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

## Deployment

### Development

```bash
uvicorn main:app --reload
```

### Production

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

Or with Gunicorn:

```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## CORS

```python
from starlette.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Session Management

```python
from starlette.middleware.sessions import SessionMiddleware

app.add_middleware(SessionMiddleware, secret_key="your-secret-key")

@router.post("/login")
async def login(request: Request, username: str = Form(...)):
    request.session["user"] = username
    return {"message": "Logged in"}

@router.get("/profile")
async def profile(request: Request):
    user = request.session.get("user")
    if not user:
        raise AuthenticationError("Not logged in")
    return {"user": user}
```

## Next Steps

- [Core Concepts](../getting_started/core_concepts.md)
- [Async Patterns](../examples/async_tasks.md)
- [Performance](../advanced/performance.md)
