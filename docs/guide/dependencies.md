# Dependencies

This guide covers the dependency injection system in FastOpenAPI.

## What are Dependencies?

Dependencies are reusable functions that can be injected into your endpoints. They're useful for:

- Database connections
- Authentication
- Authorization
- Common parameters
- Shared business logic

## Basic Dependencies

### Simple Dependency

```python
from fastopenapi import Depends

def get_query_param(q: str = Query(None)):
    return q or "default"

@router.get("/search")
def search(query: str = Depends(get_query_param)):
    return {"query": query}
```

### Dependency with Logic

```python
def get_current_user(token: str = Header(..., alias="Authorization")):
    if not token.startswith("Bearer "):
        raise AuthenticationError("Invalid token format")
    
    token_value = token[7:]  # Remove "Bearer "
    user = validate_token(token_value)
    
    if not user:
        raise AuthenticationError("Invalid token")
    
    return user

@router.get("/profile")
def get_profile(user = Depends(get_current_user)):
    return {"user": user}
```

## Database Dependencies

### Database Session

```python
from sqlalchemy.orm import Session

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ResourceNotFoundError("User not found")
    return user
```

### Async Database

```python
async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session

@router.get("/users/{user_id}")
async def get_user(user_id: int, db = Depends(get_async_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise ResourceNotFoundError("User not found")
    return user
```

## Authentication Dependencies

### Token Authentication

```python
def verify_token(authorization: str = Header(..., alias="Authorization")):
    if not authorization.startswith("Bearer "):
        raise AuthenticationError("Invalid authorization header")
    
    token = authorization[7:]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token")

@router.get("/protected")
def protected_endpoint(payload = Depends(verify_token)):
    return {"user_id": payload["user_id"]}
```

### API Key Authentication

```python
def verify_api_key(api_key: str = Header(..., alias="X-API-Key")):
    if api_key not in VALID_API_KEYS:
        raise AuthenticationError("Invalid API key")
    return api_key

@router.get("/data")
def get_data(api_key: str = Depends(verify_api_key)):
    return {"data": "sensitive"}
```

### Current User Dependency

```python
class CurrentUser:
    def __init__(self, user_id: int, username: str, roles: list[str]):
        self.user_id = user_id
        self.username = username
        self.roles = roles

def get_current_user(token: str = Header(..., alias="Authorization")) -> CurrentUser:
    payload = verify_token(token)
    user = database.get_user(payload["user_id"])
    return CurrentUser(
        user_id=user.id,
        username=user.username,
        roles=user.roles
    )

@router.get("/profile")
def get_profile(current_user: CurrentUser = Depends(get_current_user)):
    return {
        "user_id": current_user.user_id,
        "username": current_user.username
    }
```

## Authorization Dependencies

### Role-Based Access Control

```python
def require_role(required_role: str):
    def role_checker(current_user: CurrentUser = Depends(get_current_user)):
        if required_role not in current_user.roles:
            raise AuthorizationError(f"Role '{required_role}' required")
        return current_user
    return role_checker

@router.get("/admin/users")
def list_users(admin: CurrentUser = Depends(require_role("admin"))):
    return {"users": database.get_all_users()}
```

### Permission Checker

```python
def has_permission(permission: str):
    def permission_checker(current_user: CurrentUser = Depends(get_current_user)):
        if not current_user.has_permission(permission):
            raise AuthorizationError(f"Permission '{permission}' required")
        return current_user
    return permission_checker

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: CurrentUser = Depends(has_permission("users:delete"))
):
    database.delete_user(user_id)
    return {"deleted": user_id}
```

## Nested Dependencies

Dependencies can depend on other dependencies:

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    token: str = Header(..., alias="Authorization"),
    db: Session = Depends(get_db)
):
    payload = verify_token(token)
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise AuthenticationError("User not found")
    return user

def require_admin(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise AuthorizationError("Admin access required")
    return current_user

@router.get("/admin/stats")
def admin_stats(admin: User = Depends(require_admin)):
    return {"stats": get_admin_statistics()}
```

## Class-Based Dependencies

Use classes as dependencies:

```python
class Pagination:
    def __init__(
        self,
        page: int = Query(1, ge=1),
        per_page: int = Query(20, ge=1, le=100)
    ):
        self.page = page
        self.per_page = per_page
        self.skip = (page - 1) * per_page

@router.get("/items")
def list_items(pagination: Pagination = Depends()):
    items = database.get_items(
        skip=pagination.skip,
        limit=pagination.per_page
    )
    return {"items": items, "page": pagination.page}
```

### Advanced Class Dependency

```python
class SearchParams:
    def __init__(
        self,
        q: str = Query(None, description="Search query"),
        category: str = Query(None, description="Category filter"),
        min_price: float = Query(None, ge=0),
        max_price: float = Query(None, ge=0),
        sort: str = Query("created_at", description="Sort field"),
        order: str = Query("desc", pattern="^(asc|desc)$")
    ):
        self.q = q
        self.category = category
        self.min_price = min_price
        self.max_price = max_price
        self.sort = sort
        self.order = order
    
    def to_filter(self):
        filters = {}
        if self.q:
            filters["search"] = self.q
        if self.category:
            filters["category"] = self.category
        if self.min_price is not None:
            filters["min_price"] = self.min_price
        if self.max_price is not None:
            filters["max_price"] = self.max_price
        return filters

@router.get("/items")
def search_items(search: SearchParams = Depends()):
    items = database.search(
        filters=search.to_filter(),
        sort=search.sort,
        order=search.order
    )
    return {"items": items}
```

## Caching Dependencies

Dependencies are executed once per request by default:

```python
def get_db():
    print("Creating database connection")
    db = SessionLocal()
    try:
        yield db
    finally:
        print("Closing database connection")
        db.close()

@router.get("/users/{user_id}")
def get_user(
    user_id: int,
    db1: Session = Depends(get_db),  # Same instance
    db2: Session = Depends(get_db)   # Same instance
):
    # get_db() is called only once
    assert db1 is db2
    return {"user_id": user_id}
```

## Global Dependencies

Apply dependencies to all routes in a router:

```python
# This is conceptually shown - implementation may vary
admin_router = FlaskRouter()

# All routes in admin_router require admin role
@admin_router.get("/users")
def list_users(admin: User = Depends(require_admin)):
    return database.get_all_users()

@admin_router.get("/stats")
def get_stats(admin: User = Depends(require_admin)):
    return get_statistics()

main_router.include_router(admin_router, prefix="/admin")
```

## Dependency Injection Patterns

### Service Layer

```python
class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_user(self, user_id: int):
        return self.db.query(User).filter(User.id == user_id).first()
    
    def create_user(self, user_data: dict):
        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        return user

def get_user_service(db: Session = Depends(get_db)):
    return UserService(db)

@router.get("/users/{user_id}")
def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    user = service.get_user(user_id)
    if not user:
        raise ResourceNotFoundError("User not found")
    return user
```

### Repository Pattern

```python
class UserRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def find_by_id(self, user_id: int):
        return self.db.query(User).filter(User.id == user_id).first()
    
    def find_by_email(self, email: str):
        return self.db.query(User).filter(User.email == email).first()
    
    def save(self, user: User):
        self.db.add(user)
        self.db.commit()
        return user

def get_user_repository(db: Session = Depends(get_db)):
    return UserRepository(db)

@router.get("/users/{user_id}")
def get_user(
    user_id: int,
    repo: UserRepository = Depends(get_user_repository)
):
    user = repo.find_by_id(user_id)
    if not user:
        raise ResourceNotFoundError("User not found")
    return user
```

## Advanced Patterns

### Optional Dependencies

```python
def get_optional_token(authorization: str | None = Header(None, alias="Authorization")):
    if not authorization:
        return None
    
    if authorization.startswith("Bearer "):
        token = authorization[7:]
        try:
            return verify_token(token)
        except:
            return None
    return None

@router.get("/items")
def list_items(user_id: int | None = Depends(get_optional_token)):
    if user_id:
        # Return personalized results
        return get_personalized_items(user_id)
    else:
        # Return public results
        return get_public_items()
```

### Dependency Composition

```python
def verify_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_verified:
        raise AuthorizationError("Email verification required")
    return current_user

def verify_active(current_user: User = Depends(verify_user)):
    if not current_user.is_active:
        raise AuthorizationError("Account is not active")
    return current_user

@router.post("/items")
def create_item(
    item: Item,
    user: User = Depends(verify_active)  # Checks verified AND active
):
    return create_item_for_user(item, user)
```

## Testing with Dependencies

For testing, create separate test dependencies and use them directly:

```python
# Production dependency
def get_db():
    db = ProductionDatabase()
    try:
        yield db
    finally:
        db.close()

# Test dependency
def get_test_db():
    db = TestDatabase()
    try:
        yield db
    finally:
        db.close()

# In your test setup, create router with test dependencies
def test_get_user():
    from myapp import create_app

    # Create app with test configuration
    app = create_app(testing=True)
    client = app.test_client()

    response = client.get("/users/1")
    assert response.status_code == 200
```

### Mocking Dependencies

Use `unittest.mock` for more control:

```python
from unittest.mock import Mock, patch

def test_with_mocked_db():
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = {
        "id": 1,
        "name": "Test User"
    }

    with patch("myapp.dependencies.get_db", return_value=mock_db):
        response = client.get("/users/1")
        assert response.status_code == 200
```

## Common Patterns

### Rate Limiting

```python
from datetime import datetime, timedelta

rate_limit_store = {}

def rate_limit(max_requests: int = 100, window: int = 3600):
    def limiter(api_key: str = Header(..., alias="X-API-Key")):
        now = datetime.now()
        key = f"rate_limit:{api_key}"
        
        if key not in rate_limit_store:
            rate_limit_store[key] = []
        
        # Remove old requests
        rate_limit_store[key] = [
            req_time for req_time in rate_limit_store[key]
            if now - req_time < timedelta(seconds=window)
        ]
        
        # Check limit
        if len(rate_limit_store[key]) >= max_requests:
            raise AuthorizationError("Rate limit exceeded")
        
        # Add current request
        rate_limit_store[key].append(now)
        return api_key
    
    return limiter

@router.get("/api/data")
def get_data(api_key: str = Depends(rate_limit(max_requests=100))):
    return {"data": "..."}
```

### Request ID Tracking

```python
import uuid

def get_request_id(request_id: str | None = Header(None, alias="X-Request-ID")):
    if not request_id:
        request_id = str(uuid.uuid4())
    return request_id

@router.get("/items")
def list_items(request_id: str = Depends(get_request_id)):
    logger.info(f"Request {request_id}: Listing items")
    return {"items": [], "request_id": request_id}
```

### Tenant Isolation

```python
def get_tenant(tenant_id: str = Header(..., alias="X-Tenant-ID")):
    tenant = database.get_tenant(tenant_id)
    if not tenant:
        raise AuthorizationError("Invalid tenant")
    return tenant

@router.get("/items")
def list_items(tenant = Depends(get_tenant)):
    return database.get_items_for_tenant(tenant.id)
```

## Best Practices

### 1. Keep Dependencies Focused

```python
# Good - single responsibility
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Avoid - doing too much
def get_db_and_user_and_validate():
    db = SessionLocal()
    user = get_user()
    validate(user)
    return db, user
```

### 2. Use Type Hints

```python
# Good
def get_current_user() -> User:
    ...

# Avoid
def get_current_user():
    ...
```

### 3. Handle Errors Properly

```python
# Good
def get_current_user(token: str = Header(...)):
    try:
        user = validate_token(token)
        if not user:
            raise AuthenticationError("Invalid token")
        return user
    except Exception as e:
        raise AuthenticationError("Authentication failed")

# Avoid - letting exceptions leak
def get_current_user(token: str = Header(...)):
    return validate_token(token)  # May raise unexpected errors
```

### 4. Document Dependencies

```python
def get_current_user(
    authorization: str = Header(..., alias="Authorization", description="Bearer token")
) -> User:
    """
    Get the currently authenticated user.
    
    Raises:
        AuthenticationError: If token is invalid or missing
    """
    ...
```

### 5. Use Generators for Cleanup

```python
# Good - proper cleanup
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Avoid - no cleanup
def get_db():
    return SessionLocal()
```

## Next Steps

- [Security](security.md) - Security-specific dependencies
- [Error Handling](error_handling.md) - Handle dependency errors
- [Testing](../advanced/testing.md) - Test with dependencies
- [Examples](../examples/authentication.md) - Real-world examples
