# Responses API Reference

API reference for response handling in FastOpenAPI.

## Response Models

### response_model

Specify the response model for automatic validation and serialization.

```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    username: str
    email: str

@router.get("/users/{user_id}", response_model=User)
def get_user(user_id: int):
    # Return value will be validated against User model
    return {
        "id": user_id,
        "username": "john",
        "email": "john@example.com"
    }
```

### Response Validation

When `response_model` is specified, FastOpenAPI validates the response:

```python
class UserResponse(BaseModel):
    id: int
    username: str
    email: str

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    # This will raise InternalServerError (500) - missing required field 'email'
    return {"id": user_id, "username": "john"}
```

### Response Serialization

Pydantic models are automatically serialized to JSON:

```python
from datetime import datetime
from pydantic import BaseModel

class Post(BaseModel):
    id: int
    title: str
    created_at: datetime

@router.get("/posts/{post_id}", response_model=Post)
def get_post(post_id: int):
    return Post(
        id=post_id,
        title="My Post",
        created_at=datetime.now()
    )
    # Returns:
    # {
    #     "id": 1,
    #     "title": "My Post",
    #     "created_at": "2024-01-15T10:30:00"
    # }
```

---

## Status Codes

### status_code

Set the HTTP status code for the response.

```python
@router.post("/items", status_code=201)
def create_item(name: str):
    # Returns HTTP 201 Created
    return {"name": name}

@router.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int):
    # Returns HTTP 204 No Content
    # Response body is ignored for 204
    return None
```

### Common Status Codes

```python
# 200 OK (default)
@router.get("/items")
def list_items():
    return {"items": []}

# 201 Created
@router.post("/items", status_code=201)
def create_item(item: Item):
    return item

# 204 No Content
@router.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int):
    return None

# 202 Accepted
@router.post("/tasks", status_code=202)
def create_task(task: Task):
    # Task will be processed asynchronously
    return {"task_id": task.id, "status": "pending"}
```

---

## Custom Responses

### Response Class

Use the `Response` class for complete control over the response:

```python
from fastopenapi import Response

@router.get("/custom")
def custom_response():
    return Response(
        content={"message": "Success"},
        status_code=200,
        headers={
            "X-Custom-Header": "value",
            "X-Request-ID": "123456"
        }
    )
```

### Binary Responses

```python
@router.get("/download")
def download_file():
    with open("document.pdf", "rb") as f:
        content = f.read()

    return Response(
        content=content,
        status_code=200,
        headers={
            "Content-Type": "application/pdf",
            "Content-Disposition": "attachment; filename=document.pdf"
        }
    )
```

### Text Responses

```python
@router.get("/health")
def health_check():
    return Response(
        content="OK",
        status_code=200,
        headers={"Content-Type": "text/plain"}
    )
```

### Image Responses

```python
@router.get("/images/{image_id}")
def get_image(image_id: int):
    with open(f"images/{image_id}.jpg", "rb") as f:
        content = f.read()

    return Response(
        content=content,
        status_code=200,
        headers={
            "Content-Type": "image/jpeg",
            "Cache-Control": "max-age=3600"
        }
    )
```

### Tuple Responses

FastOpenAPI supports returning tuples as a shorthand for specifying content, status code, and headers:

```python
# Return (content, status_code)
@router.post("/items")
def create_item(item: Item):
    return {"id": 1, "name": item.name}, 201

# Return (content, status_code, headers)
@router.post("/items")
def create_item_with_location(item: Item):
    created_id = 1
    return (
        {"id": created_id, "name": item.name},
        201,
        {"Location": f"/items/{created_id}"}
    )
```

**Tuple formats:**

| Format | Description |
|--------|-------------|
| `(content, status)` | Content with custom status code |
| `(content, status, headers)` | Content with status code and custom headers |

This is equivalent to using the `Response` class but more concise for simple cases.

---

## Response Headers

### Custom Headers

```python
@router.get("/items")
def list_items():
    return Response(
        content={"items": []},
        headers={
            "X-Total-Count": "100",
            "X-Page": "1",
            "Cache-Control": "no-cache"
        }
    )
```

### CORS Headers

```python
@router.get("/api/data")
def get_data():
    return Response(
        content={"data": "..."},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        }
    )
```

### Cache Headers

```python
@router.get("/static/data")
def get_static_data():
    return Response(
        content={"data": "..."},
        headers={
            "Cache-Control": "public, max-age=3600",
            "ETag": "abc123"
        }
    )
```

---

## Response Types

### JSON Response (Default)

```python
@router.get("/items")
def list_items():
    # Automatically serialized to JSON
    return {"items": [1, 2, 3]}
```

### Pydantic Model Response

```python
class Item(BaseModel):
    id: int
    name: str

@router.get("/items/{item_id}", response_model=Item)
def get_item(item_id: int):
    return Item(id=item_id, name="Item")
```

### List Response

```python
@router.get("/items", response_model=list[Item])
def list_items():
    return [
        Item(id=1, name="Item 1"),
        Item(id=2, name="Item 2"),
    ]
```

### Dictionary Response

```python
@router.get("/stats")
def get_stats():
    return {
        "total_users": 100,
        "active_users": 80,
        "new_today": 5
    }
```

### None Response (204)

```python
@router.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int):
    # Delete the item...
    return None  # No content
```

---

## Response Examples

### Pagination Response

```python
from pydantic import BaseModel

class PaginatedResponse(BaseModel):
    items: list[Item]
    total: int
    page: int
    per_page: int
    total_pages: int

@router.get("/items", response_model=PaginatedResponse)
def list_items(page: int = Query(1), per_page: int = Query(10)):
    items = get_items_from_db(page, per_page)
    total = get_total_count()

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }
```

### Error Response

```python
from fastopenapi.errors import APIError

# Errors are automatically converted to this format:
{
  "error": {
    "type": "error_type",
    "message": "Error message",
    "status": 400,
    "details": {}  # Optional
  }
}
```

### Created Response

```python
@router.post("/items", status_code=201)
def create_item(item: Item):
    created_item = database.create(item)

    return Response(
        content=created_item,
        status_code=201,
        headers={
            "Location": f"/items/{created_item.id}"
        }
    )
```

### Accepted Response

```python
@router.post("/long-running-task", status_code=202)
def start_task(task_data: dict):
    task_id = queue.enqueue(task_data)

    return {
        "task_id": task_id,
        "status": "pending",
        "status_url": f"/tasks/{task_id}"
    }
```

---

## Response Model Options

### Exclude None Fields

```python
class Item(BaseModel):
    id: int
    name: str
    description: str | None = None

@router.get("/items/{item_id}", response_model=Item)
def get_item(item_id: int):
    item = Item(id=item_id, name="Item", description=None)
    return item.model_dump(exclude_none=True)
    # Returns: {"id": 1, "name": "Item"}
```

### Response Model with Exclusions

```python
class UserInDB(BaseModel):
    id: int
    username: str
    email: str
    password_hash: str  # Sensitive field

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    # password_hash excluded

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    user = get_user_from_db(user_id)
    # UserResponse automatically excludes password_hash
    return user
```

---

## Framework-Specific Responses

FastOpenAPI also supports returning framework-native response objects:

### Flask

```python
from flask import jsonify

@router.get("/items")
def list_items():
    # Return Flask's response directly
    return jsonify({"items": []})
```

### Starlette

```python
from starlette.responses import JSONResponse

@router.get("/items")
async def list_items():
    # Return Starlette's response directly
    return JSONResponse({"items": []})
```

---

## Best Practices

### 1. Always Use response_model

```python
# Good - validates response
@router.get("/users/{user_id}", response_model=User)
def get_user(user_id: int):
    return user

# Avoid - no validation
@router.get("/users/{user_id}")
def get_user(user_id: int):
    return user
```

### 2. Use Appropriate Status Codes

```python
# Good
@router.post("/items", status_code=201)
def create_item(item: Item):
    return created_item

# Avoid
@router.post("/items")  # Defaults to 200
def create_item(item: Item):
    return created_item
```

### 3. Don't Return Sensitive Data

```python
# Good - exclude sensitive fields
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    # No password_hash

# Avoid - exposes sensitive data
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    password_hash: str  # Never expose this!
```

### 4. Use Response Models for Documentation

```python
# Good - clear API documentation
@router.get("/items", response_model=list[Item])
def list_items():
    return items

# Avoid - unclear what's returned
@router.get("/items")
def list_items():
    return items
```

---

## ResponseBuilder (Internal)

The `ResponseBuilder` class handles response serialization internally. While you don't typically use it directly, understanding it helps explain response behavior.

```python
from fastopenapi.response.builder import ResponseBuilder
```

### ResponseBuilder.build()

Converts endpoint results to `Response` objects:

```python
@classmethod
def build(cls, result: Any, meta: dict) -> Response
```

**Handles:**

- Regular values (dict, list, primitives)
- Pydantic models (serialized with `model_dump(by_alias=True, mode="json")`)
- Tuple responses `(content, status)` or `(content, status, headers)`
- Response objects (returned as-is)

### Serialization Details

Pydantic models are serialized with these options:

- `by_alias=True` - Uses field aliases in output
- `mode="json"` - Ensures JSON-compatible types (dates become strings, etc.)

```python
class User(BaseModel):
    user_id: int = Field(alias="userId")
    created_at: datetime

@router.get("/user")
def get_user():
    return User(user_id=1, created_at=datetime.now())
    # Output: {"userId": 1, "created_at": "2024-01-15T10:30:00"}
```

---

## See Also

- [Response Handling Guide](../guide/response_handling.md) - Response patterns
- [Types Reference](types.md) - Response class details
- [Errors Reference](errors.md) - Error responses
- [Validation Guide](../guide/validation.md) - Response validation
