# Response Handling

This guide covers how to return and customize responses in FastOpenAPI.

## Basic Responses

### Returning Dictionaries

The simplest way to return data:

```python
@router.get("/items/{item_id}")
def get_item(item_id: int):
    return {"item_id": item_id, "name": "Item"}
```

FastOpenAPI automatically converts the dictionary to JSON.

### Returning Pydantic Models

Return Pydantic models directly:

```python
from pydantic import BaseModel

class Item(BaseModel):
    id: int
    name: str
    price: float

@router.get("/items/{item_id}")
def get_item(item_id: int):
    item = Item(id=item_id, name="Laptop", price=999.99)
    return item
```

The model is automatically serialized to JSON.

### Returning Lists

Return lists of items:

```python
@router.get("/items")
def list_items():
    return [
        {"id": 1, "name": "Item 1"},
        {"id": 2, "name": "Item 2"}
    ]
```

Or lists of models:

```python
@router.get("/items")
def list_items():
    return [
        Item(id=1, name="Item 1", price=10.0),
        Item(id=2, name="Item 2", price=20.0)
    ]
```

## Response Models

Define the response structure with `response_model`:

```python
class UserResponse(BaseModel):
    id: int
    username: str
    email: str

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    user_data = database.get_user(user_id)
    return user_data  # Validated against UserResponse
```

**Benefits:**

- Automatic validation of response data
- Documentation in OpenAPI schema
- Type safety
- Filters out extra fields

### Response Model with List

```python
@router.get("/users", response_model=list[UserResponse])
def list_users():
    users = database.get_all_users()
    return users
```

### Excluding Fields

Use different models for requests and responses:

```python
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    # password excluded

@router.post("/users", response_model=UserResponse)
def create_user(user: UserCreate):
    # Password is hashed and stored
    user_id = database.create_user(user)
    return {
        "id": user_id,
        "username": user.username,
        "email": user.email
    }
```

## Status Codes

### Setting Status Codes

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

### Common Status Codes

- `200 OK` - Successful GET, PUT, PATCH
- `201 Created` - Successful POST
- `204 No Content` - Successful DELETE
- `400 Bad Request` - Invalid request
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Not allowed
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

### Dynamic Status Codes

Return a tuple with status code:

```python
@router.post("/items")
def create_item(item: Item):
    item_id = database.create(item)
    return {"id": item_id, "name": item.name}, 201
```

Or with headers:

```python
@router.post("/items")
def create_item(item: Item):
    item_id = database.create(item)
    headers = {"X-Item-ID": str(item_id)}
    return {"id": item_id}, 201, headers
```

## Custom Response Class

Use the `Response` class for full control:

```python
from fastopenapi import Response

@router.get("/items/{item_id}")
def get_item(item_id: int):
    return Response(
        content={"item_id": item_id},
        status_code=200,
        headers={"X-Custom-Header": "value"}
    )
```

### Setting Headers

Add custom headers:

```python
@router.get("/items/{item_id}")
def get_item(item_id: int):
    return Response(
        content={"item_id": item_id},
        headers={
            "X-Request-ID": "123",
            "Cache-Control": "no-cache"
        }
    )
```

### Content-Type Header

Specify content type:

```python
@router.get("/data")
def get_data():
    csv_data = "id,name\n1,Item1\n2,Item2"
    return Response(
        content=csv_data,
        headers={"Content-Type": "text/csv"}
    )
```

## Special Response Types

### Empty Responses (204 No Content)

```python
@router.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int):
    database.delete(item_id)
    return None
```

### Redirect Responses

```python
@router.get("/old-endpoint", status_code=301)
def redirect():
    return Response(
        content=None,
        status_code=301,
        headers={"Location": "/new-endpoint"}
    )
```

### Binary Responses

Return binary data:

```python
@router.get("/download/{filename}")
def download_file(filename: str):
    file_data = read_file(filename)
    return Response(
        content=file_data,
        headers={
            "Content-Type": "application/octet-stream",
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
```

### Image Responses

```python
@router.get("/images/{image_id}")
def get_image(image_id: int):
    image_bytes = load_image(image_id)
    return Response(
        content=image_bytes,
        headers={"Content-Type": "image/jpeg"}
    )
```

### XML Responses

```python
@router.get("/data.xml")
def get_xml():
    xml_content = "<root><item>data</item></root>"
    return Response(
        content=xml_content,
        headers={"Content-Type": "application/xml"}
    )
```

## Framework-Specific Responses

You can also return framework-specific response objects:

### Flask

```python
from flask import make_response, jsonify

@router.get("/items/{item_id}")
def get_item(item_id: int):
    response = make_response(jsonify({"item_id": item_id}))
    response.headers["X-Custom"] = "value"
    return response
```

### Starlette

```python
from starlette.responses import JSONResponse

@router.get("/items/{item_id}")
async def get_item(item_id: int):
    return JSONResponse(
        content={"item_id": item_id},
        headers={"X-Custom": "value"}
    )
```

### Django

```python
from django.http import JsonResponse

@router.get("/items/{item_id}")
def get_item(item_id: int):
    return JsonResponse({"item_id": item_id})
```

## Response Validation

When `response_model` is set, responses are validated:

```python
class ItemResponse(BaseModel):
    id: int
    name: str
    price: float

@router.get("/items/{item_id}", response_model=ItemResponse)
def get_item(item_id: int):
    # This will raise InternalServerError if data doesn't match
    return {
        "id": item_id,
        "name": "Item",
        "price": "invalid"  # Wrong type!
    }
```

### Handling Validation Errors

```python
from fastopenapi.errors import InternalServerError

@router.get("/items/{item_id}", response_model=ItemResponse)
def get_item(item_id: int):
    try:
        data = database.get_item(item_id)
        return data
    except Exception as e:
        # Handle unexpected data structure
        raise InternalServerError("Failed to format response")
```

## Pagination

Common pagination pattern:

```python
class PaginatedResponse(BaseModel):
    items: list[Item]
    total: int
    page: int
    per_page: int
    total_pages: int

@router.get("/items", response_model=PaginatedResponse)
def list_items(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    offset = (page - 1) * per_page
    items = database.get_items(offset=offset, limit=per_page)
    total = database.count_items()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }
```

### Cursor-Based Pagination

```python
class CursorPaginatedResponse(BaseModel):
    items: list[Item]
    next_cursor: str | None
    prev_cursor: str | None

@router.get("/items", response_model=CursorPaginatedResponse)
def list_items(
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100)
):
    items, next_cursor = database.get_items_by_cursor(cursor, limit)
    
    return {
        "items": items,
        "next_cursor": next_cursor,
        "prev_cursor": cursor
    }
```

## Streaming Responses

For large responses, consider streaming (framework-specific):

### Starlette Streaming

```python
from starlette.responses import StreamingResponse

@router.get("/large-file")
async def stream_file():
    async def generate():
        with open("large_file.txt", "rb") as f:
            while chunk := f.read(8192):
                yield chunk
    
    return StreamingResponse(
        generate(),
        media_type="application/octet-stream"
    )
```

## Response Documentation

Document possible responses in OpenAPI:

```python
from fastopenapi.errors import ResourceNotFoundError

@router.get(
    "/items/{item_id}",
    response_model=Item,
    responses={
        200: {"description": "Item found"},
        404: {"description": "Item not found"}
    }
)
def get_item(item_id: int):
    item = database.get(item_id)
    if not item:
        raise ResourceNotFoundError(f"Item {item_id} not found")
    return item
```

## Content Negotiation

Handle different content types based on Accept header:

```python
@router.get("/items/{item_id}")
def get_item(
    item_id: int,
    accept: str = Header("application/json", alias="Accept")
):
    item = database.get(item_id)
    
    if "application/xml" in accept:
        xml = convert_to_xml(item)
        return Response(
            content=xml,
            headers={"Content-Type": "application/xml"}
        )
    
    return item  # Default JSON
```

## Caching Headers

Add cache control headers:

```python
@router.get("/items/{item_id}")
def get_item(item_id: int):
    item = database.get(item_id)
    
    return Response(
        content=item,
        headers={
            "Cache-Control": "public, max-age=3600",
            "ETag": f'"{item.id}-{item.updated_at}"'
        }
    )
```

## CORS Headers

Add CORS headers (better to use middleware):

```python
@router.get("/items")
def list_items():
    items = database.get_all()
    
    return Response(
        content=items,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE",
            "Access-Control-Allow-Headers": "Content-Type"
        }
    )
```

## Best Practices

### 1. Use Response Models

```python
# Good - validated and documented
@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    return database.get_user(user_id)

# Avoid - no validation
@router.get("/users/{user_id}")
def get_user(user_id: int):
    return database.get_user(user_id)
```

### 2. Use Correct Status Codes

```python
# Good
@router.post("/users", status_code=201)
@router.delete("/users/{user_id}", status_code=204)

# Avoid - always 200
@router.post("/users")
@router.delete("/users/{user_id}")
```

### 3. Include Helpful Metadata

```python
# Good - includes pagination metadata
{
    "items": [...],
    "total": 100,
    "page": 1,
    "per_page": 20
}

# Avoid - just data
[...]
```

### 4. Use Consistent Response Formats

```python
# Good - consistent error format
{
    "error": {
        "type": "not_found",
        "message": "User not found"
    }
}

# Avoid - inconsistent formats
{"error": "not found"}
{"message": "error occurred"}
```

### 5. Document Error Responses

```python
@router.get(
    "/users/{user_id}",
    response_model=User,
    responses={
        404: {"description": "User not found"},
        500: {"description": "Internal server error"}
    }
)
```

## Common Patterns

### Success/Error Wrapper

```python
class ApiResponse(BaseModel):
    success: bool
    data: dict | None = None
    error: str | None = None

@router.get("/items/{item_id}", response_model=ApiResponse)
def get_item(item_id: int):
    try:
        item = database.get(item_id)
        return {"success": True, "data": item}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### Partial Updates

```python
@router.patch("/items/{item_id}", response_model=Item)
def update_item(item_id: int, updates: ItemUpdate):
    item = database.get(item_id)
    updated_data = item.model_dump()
    updated_data.update(updates.model_dump(exclude_unset=True))
    
    database.update(item_id, updated_data)
    return updated_data
```

### Batch Operations

```python
class BatchResponse(BaseModel):
    success: list[int]
    failed: list[dict]

@router.post("/items/batch", response_model=BatchResponse)
def create_batch(items: list[Item]):
    success = []
    failed = []
    
    for idx, item in enumerate(items):
        try:
            item_id = database.create(item)
            success.append(item_id)
        except Exception as e:
            failed.append({"index": idx, "error": str(e)})
    
    return {"success": success, "failed": failed}
```

## Next Steps

- [Validation](validation.md) - Deep dive into Pydantic validation
- [Error Handling](error_handling.md) - Handle exceptions properly
- [Dependencies](dependencies.md) - Use dependency injection
- [Examples](../examples/crud_api.md) - See complete examples
