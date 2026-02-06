# Performance Optimization

This guide covers performance optimization techniques for FastOpenAPI applications.

## Choosing the Right Framework

Different frameworks have different performance characteristics:

### Async Frameworks (Best Performance)

**Starlette** - Best for I/O-bound workloads
```python
from starlette.applications import Starlette
from fastopenapi.routers import StarletteRouter

app = Starlette()
router = StarletteRouter(app=app)

@router.get("/data")
async def get_data():
    # Non-blocking I/O operations
    data = await fetch_from_database()
    return data
```

**Sanic** - High-performance async framework
```python
from sanic import Sanic
from fastopenapi.routers import SanicRouter

app = Sanic("MyApp")
router = SanicRouter(app=app)

@router.get("/users")
async def list_users():
    return await db.fetch_users()
```

**AioHTTP** - Async framework with good performance
```python
from aiohttp import web
from fastopenapi.routers import AioHttpRouter

app = web.Application()
router = AioHttpRouter(app=app)

@router.get("/items")
async def list_items():
    return await db.query_items()
```

### Sync Frameworks

**Flask** - Simple but slower for I/O-bound tasks
```python
from flask import Flask
from fastopenapi.routers import FlaskRouter

app = Flask(__name__)
router = FlaskRouter(app=app)

# Use for CPU-bound tasks or simple APIs
@router.get("/calculate")
def calculate():
    result = heavy_calculation()
    return {"result": result}
```

---

## Database Optimization

### Use Connection Pooling

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

# Configure connection pool
engine = create_engine(
    'postgresql://user:pass@localhost/db',
    poolclass=QueuePool,
    pool_size=20,           # Maximum number of connections
    max_overflow=10,        # Extra connections when pool is full
    pool_timeout=30,        # Timeout for getting connection
    pool_recycle=3600,      # Recycle connections after 1 hour
    pool_pre_ping=True      # Check connection health before use
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Async Database Queries

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# Async engine
async_engine = create_async_engine(
    'postgresql+asyncpg://user:pass@localhost/db',
    pool_size=20,
    max_overflow=10
)

async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session

@router.get("/users")
async def list_users(db: AsyncSession = Depends(get_async_db)):
    # Non-blocking database query
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users
```

### Batch Queries

```python
# Bad - N+1 queries
@router.get("/users-with-posts")
def get_users_with_posts():
    users = db.query(User).all()
    for user in users:
        user.posts = db.query(Post).filter(Post.user_id == user.id).all()
    return users

# Good - Single query with join
@router.get("/users-with-posts")
def get_users_with_posts():
    users = db.query(User).options(
        joinedload(User.posts)
    ).all()
    return users
```

### Use Indexes

```sql
-- Add indexes for frequently queried fields
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_posts_user_id ON posts(user_id);
CREATE INDEX idx_posts_created_at ON posts(created_at DESC);
```

---

## Caching

### In-Memory Caching

```python
from functools import lru_cache
from datetime import datetime, timedelta

# Cache function results
@lru_cache(maxsize=128)
def get_user_permissions(user_id: int):
    """Cache user permissions for quick access"""
    permissions = db.query_permissions(user_id)
    return permissions

@router.get("/permissions")
def get_my_permissions(user = Depends(get_current_user)):
    permissions = get_user_permissions(user.id)
    return {"permissions": permissions}
```

### Redis Caching

```python
import redis
import json
from datetime import timedelta

# Redis client
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)

def get_cached_or_fetch(key: str, fetch_func, ttl: int = 3600):
    """Get from cache or fetch and cache"""
    # Try to get from cache
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)

    # Fetch from source
    data = fetch_func()

    # Cache the result
    redis_client.setex(
        key,
        timedelta(seconds=ttl),
        json.dumps(data)
    )

    return data

@router.get("/popular-items")
def get_popular_items():
    """Get popular items (cached for 1 hour)"""
    return get_cached_or_fetch(
        key="popular_items",
        fetch_func=lambda: db.query_popular_items(),
        ttl=3600
    )
```

### Response Caching

```python
from flask_caching import Cache

# Configure cache
cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379/0'
})

@router.get("/stats")
@cache.cached(timeout=300)  # Cache for 5 minutes
def get_stats():
    """Expensive statistics calculation"""
    stats = calculate_statistics()
    return stats

# Cache with dynamic key
@router.get("/users/{user_id}")
@cache.cached(timeout=600, key_prefix=lambda: f"user_{request.view_args['user_id']}")
def get_user(user_id: int):
    user = db.get_user(user_id)
    return user
```

---

## Response Optimization

### Use Pagination

```python
from pydantic import BaseModel

class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    per_page: int

@router.get("/items", response_model=PaginatedResponse)
def list_items(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100)
):
    """Paginated response - don't return all data at once"""
    skip = (page - 1) * per_page

    items = db.query(Item).offset(skip).limit(per_page).all()
    total = db.query(Item).count()

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page
    }
```

### Select Only Needed Fields

```python
# Bad - fetching all fields
@router.get("/users")
def list_users():
    users = db.query(User).all()  # Gets all columns
    return users

# Good - select only needed fields
@router.get("/users")
def list_users():
    users = db.query(User.id, User.username, User.email).all()
    return [
        {"id": u.id, "username": u.username, "email": u.email}
        for u in users
    ]
```

### Response Compression

```python
from flask_compress import Compress

# Enable gzip compression
compress = Compress(app)

# Compress large responses
@router.get("/large-dataset")
def get_large_dataset():
    # Returns compressed JSON
    return {"data": large_data_list}
```

---

## Async Operations

### Parallel Async Requests

```python
import asyncio
import httpx

@router.get("/dashboard")
async def get_dashboard():
    """Fetch data from multiple sources in parallel"""

    # Sequential - slow (3 seconds total)
    # users = await fetch_users()      # 1 second
    # posts = await fetch_posts()      # 1 second
    # comments = await fetch_comments() # 1 second

    # Parallel - fast (1 second total)
    users, posts, comments = await asyncio.gather(
        fetch_users(),      # 1 second
        fetch_posts(),      # 1 second
        fetch_comments()    # 1 second
    )

    return {
        "users": users,
        "posts": posts,
        "comments": comments
    }
```

### Background Tasks

```python
import asyncio

@router.post("/send-notification", status_code=202)
async def send_notification(user_id: int, message: str):
    """Send notification asynchronously"""

    # Don't wait for completion
    asyncio.create_task(
        send_notification_async(user_id, message)
    )

    return {
        "message": "Notification queued",
        "status": "pending"
    }

async def send_notification_async(user_id: int, message: str):
    """Background task"""
    await asyncio.sleep(5)  # Simulate slow operation
    print(f"Notification sent to user {user_id}")
```

---

## Validation Optimization

### Cache Pydantic Models

FastOpenAPI automatically caches Pydantic model validation, but you can optimize further:

```python
from pydantic import BaseModel, ConfigDict

class OptimizedModel(BaseModel):
    """Optimized Pydantic model"""

    model_config = ConfigDict(
        # Faster validation
        validate_assignment=False,
        # Use slots for memory efficiency
        use_attribute_docstrings=True
    )

    id: int
    name: str
    value: float
```

### Lazy Validation

```python
# Validate only when needed
class LazyModel(BaseModel):
    data: dict  # Don't validate nested structure

    def validate_data(self):
        # Validate when accessed
        return NestedModel(**self.data)
```

---

## Connection Management

### Keep-Alive Connections

```python
import httpx

# Reuse HTTP client
http_client = httpx.AsyncClient(
    timeout=30.0,
    limits=httpx.Limits(
        max_keepalive_connections=20,
        max_connections=100
    )
)

@router.get("/external-data")
async def get_external_data():
    """Reuse HTTP connections"""
    response = await http_client.get("https://api.example.com/data")
    return response.json()
```

### Database Connection Limits

```python
# Configure based on load
engine = create_engine(
    database_url,
    pool_size=20,      # Adjust based on concurrency
    max_overflow=10,   # Extra connections when needed
    pool_timeout=30,   # Wait time for connection
)
```

---

## Profiling

### Profile Endpoints

```python
import cProfile
import pstats
from io import StringIO

@router.get("/profile/slow-endpoint")
def profile_endpoint():
    """Profile this endpoint"""
    profiler = cProfile.Profile()
    profiler.enable()

    # Your endpoint logic
    result = slow_function()

    profiler.disable()

    # Print stats
    s = StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats()
    print(s.getvalue())

    return result
```

### Monitoring

```python
import time
from functools import wraps

def measure_time(func):
    """Decorator to measure execution time"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start

        print(f"{func.__name__} took {duration:.2f} seconds")
        return result

    return wrapper

@router.get("/slow")
@measure_time
async def slow_endpoint():
    await asyncio.sleep(2)
    return {"message": "Done"}
```

---

## Best Practices

### 1. Use Async for I/O Operations

```python
# Good - async for I/O
@router.get("/data")
async def get_data(db = Depends(get_async_db)):
    result = await db.fetch_data()
    return result

# Avoid - sync for I/O in async framework
@router.get("/data")
async def get_data():
    result = db.fetch_data()  # Blocking!
    return result
```

### 2. Cache Expensive Operations

```python
# Good - cache expensive results
@lru_cache(maxsize=128)
def calculate_statistics():
    # Expensive calculation
    return stats

# Avoid - recalculate every time
def calculate_statistics():
    # Expensive calculation
    return stats
```

### 3. Use Connection Pooling

```python
# Good - connection pool
engine = create_engine(url, pool_size=20)

# Avoid - new connection each time
engine = create_engine(url, poolclass=NullPool)
```

### 4. Paginate Large Results

```python
# Good - pagination
@router.get("/items")
def list_items(page: int = 1, per_page: int = 10):
    return paginated_items(page, per_page)

# Avoid - return everything
@router.get("/items")
def list_items():
    return all_items  # Could be millions!
```

### 5. Select Only Needed Data

```python
# Good - select specific fields
db.query(User.id, User.name).all()

# Avoid - select all fields
db.query(User).all()
```

---

## Performance Checklist

- [ ] Use async framework for I/O-bound workloads
- [ ] Enable database connection pooling
- [ ] Add indexes on frequently queried fields
- [ ] Implement caching for expensive operations
- [ ] Use pagination for large datasets
- [ ] Enable response compression
- [ ] Profile slow endpoints
- [ ] Monitor database query performance
- [ ] Use async database queries
- [ ] Implement background tasks for long operations
- [ ] Optimize Pydantic model validation
- [ ] Reuse HTTP connections
- [ ] Cache static/rarely-changing data
- [ ] Use CDN for static assets

---

## See Also

- [Async Tasks Example](../examples/async_tasks.md) - Async operations
- [Framework Guides](../frameworks/overview.md) - Framework-specific optimization
- [Dependencies Guide](../guide/dependencies.md) - Optimize dependencies
