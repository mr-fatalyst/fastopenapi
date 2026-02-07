# Async Tasks Example

This example demonstrates background task processing and asynchronous operations in FastOpenAPI.

## Background Tasks with Async Frameworks

### Using Starlette

```python
import uvicorn
import asyncio
from datetime import datetime
from starlette.applications import Starlette
from pydantic import BaseModel, EmailStr
from fastopenapi import Body, Depends
from fastopenapi.routers import StarletteRouter
from fastopenapi.errors import ResourceNotFoundError

app = Starlette()
router = StarletteRouter(
    app=app,
    title="Async Tasks API",
    version="1.0.0"
)

# Task storage (in production, use database)
tasks_db = {}
task_counter = 0

class EmailTask(BaseModel):
    to: EmailStr
    subject: str
    body: str

class TaskStatus(BaseModel):
    task_id: str
    status: str
    created_at: datetime
    completed_at: datetime | None = None
    result: dict | None = None

async def send_email_async(to: str, subject: str, body: str):
    """Simulate sending email"""
    print(f"Sending email to {to}: {subject}")
    await asyncio.sleep(5)  # Simulate slow operation
    print(f"Email sent to {to}")
    return {"sent_to": to, "sent_at": datetime.now().isoformat()}

async def process_task_async(task_id: str, email_data: dict):
    """Background task processor"""
    tasks_db[task_id]["status"] = "processing"

    try:
        result = await send_email_async(
            email_data["to"],
            email_data["subject"],
            email_data["body"]
        )

        tasks_db[task_id]["status"] = "completed"
        tasks_db[task_id]["completed_at"] = datetime.now()
        tasks_db[task_id]["result"] = result
    except Exception as e:
        tasks_db[task_id]["status"] = "failed"
        tasks_db[task_id]["result"] = {"error": str(e)}

@router.post(
    "/tasks/send-email",
    response_model=dict,
    status_code=202,
    tags=["Tasks"]
)
async def create_email_task(email: EmailTask = Body(...)):
    """Create background email task"""
    global task_counter
    task_counter += 1
    task_id = f"task_{task_counter}"

    # Store task
    tasks_db[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "created_at": datetime.now(),
        "completed_at": None,
        "result": None
    }

    # Start background task
    asyncio.create_task(
        process_task_async(task_id, email.model_dump())
    )

    return {
        "task_id": task_id,
        "status": "pending",
        "message": "Email task created",
        "status_url": f"/tasks/{task_id}"
    }

@router.get(
    "/tasks/{task_id}",
    response_model=TaskStatus,
    tags=["Tasks"]
)
def get_task_status(task_id: str):
    """Get task status"""
    if task_id not in tasks_db:
        raise ResourceNotFoundError(f"Task {task_id} not found")

    return tasks_db[task_id]

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

### Testing

```bash
# Create email task
curl -X POST http://localhost:8000/tasks/send-email \
  -H "Content-Type: application/json" \
  -d '{
    "to": "user@example.com",
    "subject": "Hello",
    "body": "This is a test email"
  }'
# Returns: {"task_id": "task_1", "status": "pending", "status_url": "/tasks/task_1"}

# Check task status (immediately)
curl http://localhost:8000/tasks/task_1
# Returns: {"task_id": "task_1", "status": "processing", ...}

# Check task status (after 5+ seconds)
curl http://localhost:8000/tasks/task_1
# Returns: {"task_id": "task_1", "status": "completed", "result": {...}}
```

---

## Task Queue with Celery

```python
from celery import Celery
from pydantic import BaseModel
from fastopenapi import Body
from fastopenapi.routers import FlaskRouter
from flask import Flask

# Initialize Celery
celery_app = Celery(
    'tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

# Celery tasks
@celery_app.task(name='send_email')
def send_email_task(to: str, subject: str, body: str):
    """Celery task for sending emails"""
    import time
    print(f"Sending email to {to}")
    time.sleep(5)  # Simulate slow operation
    print(f"Email sent to {to}")
    return {"sent_to": to, "subject": subject}

@celery_app.task(name='generate_report')
def generate_report_task(report_type: str, filters: dict):
    """Generate report in background"""
    import time
    print(f"Generating {report_type} report...")
    time.sleep(10)
    return {
        "report_type": report_type,
        "file_url": f"/reports/{report_type}.pdf"
    }

# Flask API
app = Flask(__name__)
router = FlaskRouter(
    app=app,
    title="Celery Tasks API",
    version="1.0.0"
)

class EmailRequest(BaseModel):
    to: str
    subject: str
    body: str

class ReportRequest(BaseModel):
    report_type: str
    filters: dict = {}

@router.post("/tasks/send-email", status_code=202, tags=["Tasks"])
def create_email_task(email: EmailRequest = Body(...)):
    """Queue email task"""
    task = send_email_task.delay(email.to, email.subject, email.body)

    return {
        "task_id": task.id,
        "status": "pending",
        "status_url": f"/tasks/{task.id}"
    }

@router.post("/tasks/generate-report", status_code=202, tags=["Tasks"])
def create_report_task(report: ReportRequest = Body(...)):
    """Queue report generation task"""
    task = generate_report_task.delay(report.report_type, report.filters)

    return {
        "task_id": task.id,
        "status": "pending",
        "status_url": f"/tasks/{task.id}"
    }

@router.get("/tasks/{task_id}", tags=["Tasks"])
def get_task_status(task_id: str):
    """Get task status"""
    from celery.result import AsyncResult

    task = AsyncResult(task_id, app=celery_app)

    response = {
        "task_id": task_id,
        "status": task.state,
        "result": None
    }

    if task.state == "SUCCESS":
        response["result"] = task.result
    elif task.state == "FAILURE":
        response["error"] = str(task.info)

    return response

if __name__ == "__main__":
    app.run(debug=True)
```

---

## Async Database Operations

```python
import uvicorn
from starlette.applications import Starlette
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from pydantic import BaseModel
from fastopenapi import Depends
from fastopenapi.routers import StarletteRouter
from fastopenapi.errors import ResourceNotFoundError

app = Starlette()
router = StarletteRouter(app=app)

# Async database setup
engine = create_async_engine("sqlite+aiosqlite:///./test.db")
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_async_db():
    """Async database session dependency"""
    async with AsyncSessionLocal() as session:
        yield session

class User(BaseModel):
    id: int
    username: str
    email: str

@router.get("/users", response_model=list[User], tags=["Users"])
async def list_users(db: AsyncSession = Depends(get_async_db)):
    """List users (async database query)"""
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users

@router.get("/users/{user_id}", response_model=User, tags=["Users"])
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """Get user by ID (async)"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise ResourceNotFoundError(f"User {user_id} not found")

    return user

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

---

## Parallel Async Operations

```python
import asyncio
import httpx
from starlette.applications import Starlette
from fastopenapi.routers import StarletteRouter

app = Starlette()
router = StarletteRouter(app=app)

async def fetch_user(user_id: int):
    """Fetch user from external API"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/users/{user_id}")
        return response.json()

async def fetch_posts(user_id: int):
    """Fetch user's posts from external API"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/users/{user_id}/posts")
        return response.json()

async def fetch_comments(user_id: int):
    """Fetch user's comments"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/users/{user_id}/comments")
        return response.json()

@router.get("/users/{user_id}/profile", tags=["Users"])
async def get_user_profile(user_id: int):
    """Get complete user profile (parallel async requests)"""

    # Fetch all data in parallel
    user, posts, comments = await asyncio.gather(
        fetch_user(user_id),
        fetch_posts(user_id),
        fetch_comments(user_id)
    )

    return {
        "user": user,
        "posts": posts,
        "comments": comments
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

---

## Streaming Responses

```python
import asyncio
from starlette.responses import StreamingResponse
from fastopenapi.routers import StarletteRouter

router = StarletteRouter()

async def generate_data():
    """Generate data stream"""
    for i in range(100):
        await asyncio.sleep(0.1)
        yield f"data: {i}\n\n"

@router.get("/stream", tags=["Streaming"])
async def stream_data():
    """Server-Sent Events (SSE) endpoint"""
    return StreamingResponse(
        generate_data(),
        media_type="text/event-stream"
    )

async def generate_csv():
    """Generate CSV data stream"""
    yield "id,name,email\n"
    for i in range(1000):
        await asyncio.sleep(0.01)
        yield f"{i},User{i},user{i}@example.com\n"

@router.get("/export/users.csv", tags=["Export"])
async def export_users():
    """Stream large CSV export"""
    return StreamingResponse(
        generate_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users.csv"}
    )
```

---

## WebSocket Support

```python
import uvicorn
from starlette.applications import Starlette
from starlette.websockets import WebSocket
from fastopenapi.routers import StarletteRouter

app = Starlette()
router = StarletteRouter(app=app)

# Active WebSocket connections
active_connections: list[WebSocket] = []

@router.get("/chat", tags=["WebSocket"])
async def chat_info():
    """Get chat info"""
    return {
        "active_connections": len(active_connections),
        "websocket_url": "ws://localhost:8000/ws/chat"
    }

# WebSocket endpoint (not handled by router, added directly to app)
@app.websocket_route("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket chat endpoint"""
    await websocket.accept()
    active_connections.append(websocket)

    try:
        while True:
            # Receive message
            data = await websocket.receive_text()

            # Broadcast to all connections
            for connection in active_connections:
                await connection.send_text(f"Message: {data}")
    except:
        pass
    finally:
        active_connections.remove(websocket)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

---

## Scheduled Tasks

```python
import asyncio
from datetime import datetime
from starlette.applications import Starlette
from fastopenapi.routers import StarletteRouter

app = Starlette()
router = StarletteRouter(app=app)

# Task scheduler
async def cleanup_task():
    """Runs every hour"""
    while True:
        print(f"Running cleanup at {datetime.now()}")
        # Perform cleanup
        await asyncio.sleep(3600)  # 1 hour

async def stats_update_task():
    """Updates stats every 5 minutes"""
    while True:
        print(f"Updating stats at {datetime.now()}")
        # Update statistics
        await asyncio.sleep(300)  # 5 minutes

@app.on_event("startup")
async def startup_tasks():
    """Start background tasks on startup"""
    asyncio.create_task(cleanup_task())
    asyncio.create_task(stats_update_task())

@router.get("/health", tags=["Health"])
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

---

## Rate Limiting with Async

```python
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
from fastopenapi import Depends, Header
from fastopenapi.errors import AuthorizationError

class AsyncRateLimiter:
    """Async rate limiter"""

    def __init__(self, max_requests: int = 100, window: int = 3600):
        self.max_requests = max_requests
        self.window = window
        self.requests = defaultdict(list)
        self.lock = asyncio.Lock()

    async def check_rate_limit(self, key: str):
        """Check if request is within rate limit"""
        async with self.lock:
            now = datetime.now()
            window_start = now - timedelta(seconds=self.window)

            # Remove old requests
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if req_time > window_start
            ]

            # Check limit
            if len(self.requests[key]) >= self.max_requests:
                raise AuthorizationError("Rate limit exceeded")

            # Add current request
            self.requests[key].append(now)

rate_limiter = AsyncRateLimiter(max_requests=100, window=3600)

async def check_rate_limit(user_id: str = Header(..., alias="X-User-ID")):
    """Rate limit dependency"""
    await rate_limiter.check_rate_limit(user_id)

@router.get("/api/data")
async def get_data(_: None = Depends(check_rate_limit)):
    """Rate-limited endpoint"""
    return {"data": "..."}
```

---

## Best Practices

### 1. Use Async for I/O-Bound Operations

```python
# Good - async for network/database operations
@router.get("/users")
async def list_users(db = Depends(get_async_db)):
    users = await db.fetch_users()
    return users

# Avoid - sync for I/O operations in async framework
@router.get("/users")
def list_users():
    users = database.fetch_users()  # Blocking!
    return users
```

### 2. Background Tasks for Long Operations

```python
# Good - return immediately, process in background
@router.post("/reports", status_code=202)
async def create_report(report_type: str):
    task_id = await queue_report_task(report_type)
    return {"task_id": task_id, "status": "pending"}

# Avoid - blocking the request
@router.post("/reports")
async def create_report(report_type: str):
    report = await generate_report(report_type)  # Takes 10 minutes!
    return report
```

### 3. Use Task Status Endpoints

```python
# Create task endpoint
@router.post("/tasks", status_code=202)
async def create_task():
    task_id = create_background_task()
    return {"task_id": task_id, "status_url": f"/tasks/{task_id}"}

# Status endpoint
@router.get("/tasks/{task_id}")
def get_task_status(task_id: str):
    return {"status": "completed", "result": {...}}
```

### 4. Handle Task Failures Gracefully

```python
try:
    result = await process_task()
    task["status"] = "completed"
    task["result"] = result
except Exception as e:
    task["status"] = "failed"
    task["error"] = str(e)
```

### 5. Use Proper Async Dependencies

```python
# Good - async dependency
async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session

# Avoid - sync dependency in async framework
def get_db():
    db = SessionLocal()  # Blocking!
    yield db
```

---

## See Also

- [Dependencies Guide](../guide/dependencies.md) - Async dependencies
- [Starlette Framework](../frameworks/starlette.md) - Async framework guide
- [Performance Guide](../advanced/performance.md) - Optimization tips
