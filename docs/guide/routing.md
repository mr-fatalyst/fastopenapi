# Routing

This guide covers how to define routes and endpoints in FastOpenAPI.

## Basic Routing

Use decorator methods on your router to define endpoints:

```python
from fastopenapi.routers import FlaskRouter
from flask import Flask

app = Flask(__name__)
router = FlaskRouter(app=app)

@router.get("/")
def root():
    return {"message": "Hello, World!"}

@router.get("/items")
def list_items():
    return {"items": ["item1", "item2"]}
```

## HTTP Methods

FastOpenAPI supports all standard HTTP methods:

### GET

Retrieve resources:

```python
@router.get("/items")
def list_items():
    return {"items": []}

@router.get("/items/{item_id}")
def get_item(item_id: int):
    return {"item_id": item_id}
```

### POST

Create new resources:

```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float

@router.post("/items", status_code=201)
def create_item(item: Item):
    # Save item to database
    return item
```

### PUT

Replace entire resources:

```python
@router.put("/items/{item_id}")
def replace_item(item_id: int, item: Item):
    # Replace the entire item
    return {"item_id": item_id, **item.model_dump()}
```

### PATCH

Partially update resources:

```python
class ItemUpdate(BaseModel):
    name: str | None = None
    price: float | None = None

@router.patch("/items/{item_id}")
def update_item(item_id: int, updates: ItemUpdate):
    # Update only provided fields
    return {"item_id": item_id, "updated": True}
```

### DELETE

Remove resources:

```python
@router.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int):
    # Delete item from database
    return None  # 204 No Content
```

### HEAD

Get headers without body (useful for checking existence):

```python
@router.head("/items/{item_id}")
def check_item(item_id: int):
    # Check if item exists
    exists = database.exists(item_id)
    if not exists:
        raise ResourceNotFoundError()
    return None
```

### OPTIONS

Get allowed methods (usually handled automatically):

```python
@router.options("/items/{item_id}")
def item_options():
    return None
```

## Path Parameters

Extract values from the URL path:

```python
@router.get("/users/{user_id}")
def get_user(user_id: int):
    return {"user_id": user_id}

@router.get("/users/{user_id}/posts/{post_id}")
def get_user_post(user_id: int, post_id: int):
    return {"user_id": user_id, "post_id": post_id}
```

### Type Conversion

Path parameters are automatically converted to the specified type:

```python
@router.get("/items/{item_id}")
def get_item(item_id: int):
    # item_id is guaranteed to be an int
    # /items/abc returns 422 error
    return {"item_id": item_id, "type": type(item_id).__name__}
```

### Path with Documentation

Use the `Path` class for additional documentation:

```python
from fastopenapi import Path

@router.get("/items/{item_id}")
def get_item(
    item_id: int = Path(..., description="The ID of the item to retrieve", ge=1)
):
    return {"item_id": item_id}
```

Parameters:

- `...` - Required (no default value)
- `description` - Shown in docs
- `ge=1` - Greater than or equal to 1
- `le=100` - Less than or equal to 100
- `gt=0` - Greater than 0
- `lt=100` - Less than 100

## Route Metadata

### Tags

Group endpoints in documentation:

```python
@router.get("/users", tags=["Users"])
def list_users():
    return []

@router.post("/users", tags=["Users"])
def create_user(user: User):
    return user

@router.get("/items", tags=["Items"])
def list_items():
    return []
```

In Swagger UI, endpoints are grouped under their tags.

### Status Codes

Specify the success status code:

```python
@router.get("/items/{item_id}", status_code=200)  # Default
def get_item(item_id: int):
    return {"item_id": item_id}

@router.post("/items", status_code=201)  # Created
def create_item(item: Item):
    return item

@router.delete("/items/{item_id}", status_code=204)  # No Content
def delete_item(item_id: int):
    database.delete(item_id)
    return None
```

### Response Model

Define the response structure:

```python
class UserResponse(BaseModel):
    id: int
    username: str
    email: str

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    user = database.get_user(user_id)
    return user  # Validated against UserResponse
```

### Docstrings

Function docstrings appear in the documentation:

```python
@router.get("/items/{item_id}")
def get_item(item_id: int):
    """
    Retrieve an item by ID.
    
    This endpoint returns detailed information about a specific item.
    """
    return {"item_id": item_id}
```

## Multiple Routes for One Function

You can register the same function under multiple paths:

```python
@router.get("/items")
@router.get("/products")
def list_items():
    return {"items": []}
```

Or use the router's `add_route` method:

```python
def list_items():
    return {"items": []}

router.add_route("/items", "GET", list_items)
router.add_route("/products", "GET", list_items)
```

## Sub-Routers

Organize large applications with sub-routers:

### Creating a Sub-Router

```python
# users.py
from fastopenapi.routers import FlaskRouter

users_router = FlaskRouter()

@users_router.get("/")
def list_users():
    return {"users": []}

@users_router.get("/{user_id}")
def get_user(user_id: int):
    return {"user_id": user_id}

@users_router.post("/", status_code=201)
def create_user(user: User):
    return user
```

### Including Sub-Routers

```python
# main.py
from flask import Flask
from fastopenapi.routers import FlaskRouter
from users import users_router

app = Flask(__name__)
main_router = FlaskRouter(app=app)

# Include users router under /users prefix
main_router.include_router(users_router, prefix="/users")

# Routes are now:
# GET  /users/
# GET  /users/{user_id}
# POST /users/
```

### Nested Sub-Routers

You can nest routers multiple levels deep:

```python
# api/v1/users.py
users_router = FlaskRouter()

@users_router.get("/")
def list_users():
    return []

# api/v1/__init__.py
v1_router = FlaskRouter()
v1_router.include_router(users_router, prefix="/users")

# main.py
main_router = FlaskRouter(app=app)
main_router.include_router(v1_router, prefix="/api/v1")

# Final route: GET /api/v1/users/
```

### Sub-Router Tags

Apply tags to all routes in a sub-router:

```python
# When including, you can override tags
# (Note: This requires manually adding tags to each route)
users_router = FlaskRouter()

@users_router.get("/", tags=["Users"])
def list_users():
    return []

@users_router.post("/", tags=["Users"])
def create_user(user: User):
    return user

main_router.include_router(users_router, prefix="/users")
```

## Router Configuration

Configure the router when creating it:

```python
router = FlaskRouter(
    app=app,
    title="My API",                    # API title
    version="1.0.0",                   # API version
    description="My API documentation", # Description
    docs_url="/docs",                  # Swagger UI path
    redoc_url="/redoc",                # ReDoc path
    openapi_url="/openapi.json",       # OpenAPI schema path
    openapi_version="3.0.0",           # OpenAPI spec version
)
```

### Disabling Documentation

To disable documentation endpoints:

```python
router = FlaskRouter(
    app=app,
    docs_url=None,         # No Swagger UI
    redoc_url=None,        # No ReDoc
    openapi_url=None,      # No OpenAPI JSON
)
```

### Custom Documentation URLs

Use custom paths for documentation:

```python
router = FlaskRouter(
    app=app,
    docs_url="/api-docs",           # Custom Swagger UI path
    redoc_url="/api-documentation", # Custom ReDoc path
    openapi_url="/api-schema.json", # Custom schema path
)
```

## Route Order and Priority

Routes are matched in the order they're defined. More specific routes should come before generic ones:

```python
# Good - specific before generic
@router.get("/items/featured")
def get_featured_items():
    return {"items": ["featured1", "featured2"]}

@router.get("/items/{item_id}")
def get_item(item_id: int):
    return {"item_id": item_id}

# Bad - generic catches everything
@router.get("/items/{item_id}")
def get_item(item_id: int):
    return {"item_id": item_id}

@router.get("/items/featured")  # This will never be reached!
def get_featured_items():
    return {"items": ["featured1", "featured2"]}
```

## Advanced Route Patterns

### Optional Path Segments

Use query parameters instead of optional path segments:

```python
# Don't do this:
# /items/{item_id?}

# Do this:
@router.get("/items")
def get_items(item_id: int | None = Query(None)):
    if item_id:
        return {"item": item_id}
    return {"items": []}
```

### Multiple Path Types

```python
# String path
@router.get("/categories/{category_name}")
def get_category(category_name: str):
    return {"category": category_name}

# Integer path
@router.get("/items/{item_id}")
def get_item(item_id: int):
    return {"item_id": item_id}
```

### Path with Regex (Framework-specific)

Some frameworks support regex in paths. Check your framework's documentation:

```python
# Flask example with regex converter
@router.get("/users/<regex('[a-z]+'):username>")
def get_user(username: str):
    return {"username": username}
```

## Best Practices

### 1. Use Descriptive Names

```python
# Good
@router.get("/users/{user_id}")
def get_user(user_id: int):
    pass

# Bad
@router.get("/users/{id}")
def get(id: int):
    pass
```

### 2. Follow REST Conventions

```python
# Collection operations
@router.get("/items")        # List items
@router.post("/items")       # Create item

# Resource operations
@router.get("/items/{id}")    # Get item
@router.put("/items/{id}")    # Replace item
@router.patch("/items/{id}")  # Update item
@router.delete("/items/{id}") # Delete item
```

### 3. Use Plural Nouns for Collections

```python
# Good
@router.get("/users")
@router.get("/items")

# Avoid
@router.get("/user")
@router.get("/item")
```

### 4. Version Your API

```python
# Use URL versioning
main_router.include_router(v1_router, prefix="/api/v1")
main_router.include_router(v2_router, prefix="/api/v2")
```

### 5. Use Nouns, Not Verbs

```python
# Good
@router.post("/items")        # Create an item
@router.delete("/items/{id}") # Delete an item

# Avoid
@router.post("/create-item")
@router.post("/delete-item")
```

## Next Steps

- [Request Parameters](request_parameters.md) - Query, header, cookie parameters
- [Request Body](request_body.md) - Handle JSON, forms, and files
- [Response Handling](response_handling.md) - Customize responses
- [Error Handling](error_handling.md) - Handle exceptions
