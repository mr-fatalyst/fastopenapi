# BaseRouter API

The `BaseRouter` class is central to FastOpenAPI.

## Constructor

```python
BaseRouter(app, docs_url="/docs", openapi_version="3.0.3", title="API", description="", version="1.0.0")
```

### Arguments

- `app`: Framework-specific app instance. It's required only for main router.
- `docs_url`: URL for Swagger UI.
- `redoc_url`: URL for ReDoc.
- `openapi_version`: OpenAPI spec version.
- `title`: API title.
- `description`: API description.
- `version`: API version.

### Methods

- `.get(path, response_model, tags, status_code)`
- `.post(path, response_model, tags, status_code)`
- `.patch(path, response_model, tags, status_code)`
- `.put(path, response_model, tags, status_code)`
- `.delete(path, response_model, tags, status_code)`
- `.include_router(router, prefix="")`: Include other router instances for modularity.

---

## Methods: get / post / patch / put / delete

These methods use as decorators. These allow to add GET / POST / PATCH / PUT / DELETE method to routes.

```python
from pydantic import BaseModel
from typing import Optional

# Don't use this router. It's just an example.
from fastopenapi.base_router import BaseRouter

class CreateUserRequest(BaseModel):
    name: str
    surname: str
    age: int

class UpdateUserRequest(BaseModel):
    name: Optional[str]
    surname: Optional[str]
    age: Optional[int]

class UserResponse(BaseModel):
    id: int
    name: str
    surname: str
    age: int

router = BaseRouter()
    
@router.get("/user/{user_id}", tags=["User"], status_code=200, response_model=UserResponse)
def get_user(user_id: int):
    # your getting logic here
    data = {}
    return UserResponse(**data)

@router.post("/user", tags=["User"], status_code=201, response_model=UserResponse)
def create_user(user_data: CreateUserRequest):
    # your creating logic here
    data = {}
    return UserResponse(**data)

@router.patch("/user/{user_id}", tags=["User"], status_code=200, response_model=UserResponse)
def update_user(user_id: int, user_data: UpdateUserRequest):
    # your updating logic here
    data = {}
    return UserResponse(**data)

@router.delete("/user/{user_id}", tags=["User"], status_code=204)
def delete_user(user_id: int):
    # your deleting logic here
    return None
```

---

## Method: include_router

Allows modular router inclusion.

```python
include_router(router, prefix="")
```

### Arguments

- `router`: Another FastOpenAPI router instance to include.
- `prefix`: Optional URL prefix.

### Example

```python
api_router = BaseRouter(app)
users_router = BaseRouter(app)

@router.get("/users")
async def users(): pass

router.include_router(users_router, prefix="/api/v1")
```

---

[<< Back](index.md)