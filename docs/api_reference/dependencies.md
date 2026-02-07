# Dependencies API Reference

API reference for dependency injection classes.

## Depends

Marker class for dependency injection.

```python
from fastopenapi import Depends
```

### Class Definition

```python
class Depends:
    def __init__(self, dependency: Callable[..., Any] | None = None)
```

### Parameters

- **dependency** (`Callable | None`): Function or callable class to execute for dependency injection. If `None`, uses the parameter's type annotation as the dependency.

### Attributes

- **dependency** (`Callable`): The dependency function

### Usage

#### Function Dependency

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users
```

#### Class Dependency

```python
class Pagination:
    def __init__(
        self,
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=100)
    ):
        self.page = page
        self.per_page = per_page

@router.get("/items")
def list_items(pagination: Pagination = Depends()):
    # pagination is an instance of Pagination
    return {
        "page": pagination.page,
        "per_page": pagination.per_page
    }
```

#### Auto-Resolution

When `dependency` is `None`, FastOpenAPI uses the parameter's type annotation:

```python
class UserService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def get_user(self, user_id: int):
        return self.db.query(User).filter(User.id == user_id).first()

@router.get("/users/{user_id}")
def get_user(
    user_id: int,
    service: UserService = Depends()  # UserService will be called
):
    return service.get_user(user_id)
```

---

## Security

Security dependency with OAuth2 scopes support.

```python
from fastopenapi import Security
```

### Class Definition

```python
class Security(Depends):
    def __init__(
        self,
        dependency: Callable[..., Any] | None = None,
        *,
        scopes: Sequence[str] | None = None,
    )
```

### Parameters

- **dependency** (`Callable | None`): Security validation function
- **scopes** (`Sequence[str] | None`): Required OAuth2 scopes

### Attributes

- **dependency** (`Callable`): The security function
- **scopes** (`list[str]`): List of required scopes

### Usage

#### Basic Security

```python
def verify_token(authorization: str = Header(..., alias="Authorization")):
    if not authorization.startswith("Bearer "):
        raise AuthenticationError("Invalid authorization header")

    token = authorization[7:]
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    return payload

@router.get("/protected")
def protected_route(user = Security(verify_token)):
    return {"user_id": user["user_id"]}
```

#### OAuth2 Scopes

```python
from fastopenapi import Security, SecurityScopes

def verify_scopes(
    authorization: str = Header(..., alias="Authorization"),
    security_scopes: SecurityScopes,
):
    token = authorization[7:]
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

    # Check if user has required scopes
    user_scopes = payload.get("scopes", [])
    for scope in security_scopes.scopes:
        if scope not in user_scopes:
            raise SecurityError(f"Scope '{scope}' required")

    return payload

@router.get("/admin/users")
def list_all_users(
    user = Security(verify_scopes, scopes=["admin:read"])
):
    return database.get_all_users()

@router.delete("/admin/users/{user_id}")
def delete_user(
    user_id: int,
    user = Security(verify_scopes, scopes=["admin:write", "users:delete"])
):
    database.delete_user(user_id)
    return {"deleted": user_id}
```

#### Multiple Scopes

```python
@router.post("/posts")
def create_post(
    content: str,
    user = Security(verify_scopes, scopes=["posts:write", "posts:create"])
):
    # User must have BOTH scopes
    return create_post(content, user["user_id"])
```

---

## SecurityScopes

Scopes injected into security dependency functions.

```python
from fastopenapi import SecurityScopes
```

### Class Definition

```python
class SecurityScopes:
    def __init__(self, scopes: list[str] | None = None)
```

### Parameters

- **scopes** (`list[str] | None`): List of required scopes. Defaults to `[]`.

### Attributes

- **scopes** (`list[str]`): List of required scopes

### Usage

Add a `SecurityScopes`-annotated parameter to your security function. FastOpenAPI will automatically inject the scopes from the `Security()` declaration:

```python
from fastopenapi import Security, SecurityScopes

def verify_token(
    authorization: str = Header(..., alias="Authorization"),
    security_scopes: SecurityScopes,
):
    token = authorization[7:]
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

    for scope in security_scopes.scopes:
        if scope not in payload.get("scopes", []):
            raise SecurityError(f"Missing scope: {scope}")

    return payload

# security_scopes.scopes will be ["admin:read"]
@router.get("/admin")
def admin(user=Security(verify_token, scopes=["admin:read"])):
    return {"user": user}
```

---

## Dependency Features

### Request-Scoped Caching

Dependencies are cached per request. If the same dependency is used multiple times in a single request, it's executed only once:

```python
def get_db():
    print("Creating DB connection")  # Printed once per request
    db = SessionLocal()
    try:
        yield db
    finally:
        print("Closing DB connection")  # Called once per request
        db.close()

@router.get("/users/{user_id}")
def get_user(
    user_id: int,
    db1: Session = Depends(get_db),  # Same instance
    db2: Session = Depends(get_db),  # Same instance
):
    assert db1 is db2  # True
    return {"user_id": user_id}
```

### Nested Dependencies

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
    db: Session = Depends(get_db)  # Nested dependency
):
    payload = verify_token(token)
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise AuthenticationError("User not found")
    return user

def require_admin(
    current_user: User = Depends(get_current_user)  # Nested dependency
):
    if not current_user.is_admin:
        raise AuthorizationError("Admin required")
    return current_user

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    admin: User = Depends(require_admin)
):
    # Dependency chain: get_db -> get_current_user -> require_admin
    return {"deleted": user_id}
```

### Circular Dependency Detection

FastOpenAPI automatically detects circular dependencies:

```python
def dependency_a(b = Depends(dependency_b)):
    return b

def dependency_b(a = Depends(dependency_a)):
    return a

@router.get("/test")
def test(result = Depends(dependency_a)):
    # Raises CircularDependencyError
    return result
```

### Generator Dependencies

Use `yield` for setup/teardown:

```python
def get_db():
    db = SessionLocal()
    try:
        yield db  # This value is injected
    finally:
        db.close()  # Cleanup always runs

@router.get("/users")
def list_users(db = Depends(get_db)):
    # db is the yielded value
    # db.close() called after response is returned
    return db.query(User).all()
```

### Async Dependencies

```python
async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session

@router.get("/users")
async def list_users(db = Depends(get_async_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users
```

---

## Common Patterns

### Database Session

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/items")
def list_items(db: Session = Depends(get_db)):
    return db.query(Item).all()
```

### Current User

```python
def get_current_user(
    authorization: str = Header(..., alias="Authorization"),
    db: Session = Depends(get_db)
):
    token = authorization.replace("Bearer ", "")
    payload = verify_token(token)
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise AuthenticationError("Invalid token")
    return user

@router.get("/profile")
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user
```

### Pagination

```python
class Pagination:
    def __init__(
        self,
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=100)
    ):
        self.page = page
        self.per_page = per_page
        self.skip = (page - 1) * per_page

@router.get("/items")
def list_items(
    pagination: Pagination = Depends(),
    db: Session = Depends(get_db)
):
    items = db.query(Item).offset(pagination.skip).limit(pagination.per_page).all()
    return {"items": items, "page": pagination.page}
```

### Service Layer

```python
class UserService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def get_user(self, user_id: int):
        return self.db.query(User).filter(User.id == user_id).first()

    def create_user(self, user_data: dict):
        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        return user

@router.get("/users/{user_id}")
def get_user(
    user_id: int,
    service: UserService = Depends()
):
    user = service.get_user(user_id)
    if not user:
        raise ResourceNotFoundError(f"User {user_id} not found")
    return user
```

---

## DependencyResolver (Internal)

The `DependencyResolver` class handles the internal resolution of dependencies. While you typically don't need to interact with it directly, understanding it can be useful for advanced use cases.

```python
from fastopenapi.core.dependency_resolver import (
    DependencyResolver,
    resolve_dependencies,
    resolve_dependencies_async,
    get_dependency_stats,
)
```

### Features

- **Request-scoped caching**: Dependencies are resolved once per request
- **Recursive resolution**: Dependencies can have their own dependencies
- **Circular dependency detection**: Automatically detects and reports circular dependencies
- **Security scopes injection**: Injects `SecurityScopes` into security dependency functions
- **Thread-safe operation**: Safe for concurrent requests

### Convenience Functions

#### resolve_dependencies()

Resolve dependencies synchronously:

```python
from fastopenapi.core.dependency_resolver import resolve_dependencies

# Typically called internally by the router
kwargs = resolve_dependencies(endpoint_function, request_data)
result = endpoint_function(**kwargs)
```

#### resolve_dependencies_async()

Resolve dependencies asynchronously:

```python
from fastopenapi.core.dependency_resolver import resolve_dependencies_async

# For async endpoints
kwargs = await resolve_dependencies_async(endpoint_function, request_data)
result = await endpoint_function(**kwargs)
```

#### get_dependency_stats()

Get cache statistics for monitoring:

```python
from fastopenapi.core.dependency_resolver import get_dependency_stats

stats = get_dependency_stats()
# {"active_requests": 5, "execution_locks": 10}
```

---

## See Also

- [Dependencies Guide](../guide/dependencies.md) - Comprehensive dependency injection guide
- [Security Guide](../guide/security.md) - Security and authentication
- [Authentication Example](../examples/authentication.md) - Authentication examples
- [Errors Reference](errors.md) - Error classes (AuthenticationError, SecurityError, etc.)
