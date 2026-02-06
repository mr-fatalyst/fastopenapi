# Types API Reference

Core type definitions in FastOpenAPI.

## FileUpload

Framework-agnostic file upload container with unified API.

```python
from fastopenapi import FileUpload
```

### Class Definition

```python
class FileUpload:
    def __init__(
        self,
        filename: str,
        content_type: str | None = None,
        size: int | None = None,
        file: Any = None,
    )
```

### Attributes

- **filename** (`str`): Name of the uploaded file
- **content_type** (`str`): MIME type of the file (default: `"application/octet-stream"`)
- **size** (`int | None`): File size in bytes
- **file** (`Any`): Native framework file object (accessed via `.file` property)

### Methods

#### read()

Read entire file content synchronously.

```python
def read() -> bytes
```

**Returns**: File contents as bytes

**Example**:
```python
@router.post("/upload")
def upload(file: FileUpload = File(...)):
    content = file.read()
    return {"size": len(content)}
```

#### aread()

Read entire file content asynchronously.

```python
async def aread() -> bytes
```

**Returns**: File contents as bytes

**Example**:
```python
@router.post("/upload")
async def upload(file: FileUpload = File(...)):
    content = await file.aread()
    return {"size": len(content)}
```

### Usage Example

```python
from fastopenapi import File, FileUpload
from fastopenapi.routers import FlaskRouter

router = FlaskRouter()

@router.post("/upload")
def upload_file(
    file: FileUpload = File(..., description="File to upload")
):
    # Access file metadata
    print(f"Filename: {file.filename}")
    print(f"Content-Type: {file.content_type}")
    print(f"Size: {file.size} bytes")

    # Read file content
    content = file.read()

    # Process the file...

    return {
        "filename": file.filename,
        "size": file.size,
        "content_type": file.content_type
    }
```

### Async Example

```python
from fastopenapi.routers import StarletteRouter

router = StarletteRouter()

@router.post("/upload")
async def upload_file(file: FileUpload = File(...)):
    content = await file.aread()

    # Save to disk
    with open(f"uploads/{file.filename}", "wb") as f:
        f.write(content)

    return {"filename": file.filename, "size": len(content)}
```

---

## Response

Custom response with headers and status code control.

```python
from fastopenapi import Response
```

### Class Definition

```python
class Response:
    def __init__(
        self,
        content: Any,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    )
```

### Attributes

- **content** (`Any`): Response body (can be dict, list, str, bytes, Pydantic model)
- **status_code** (`int`): HTTP status code (default: `200`)
- **headers** (`dict[str, str]`): HTTP response headers

### Usage Example

```python
from fastopenapi import Response

@router.get("/custom")
def custom_response():
    return Response(
        content={"message": "Success"},
        status_code=201,
        headers={
            "X-Custom-Header": "value",
            "X-Request-ID": "123"
        }
    )
```

### Binary Response

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

### Text Response

```python
@router.get("/health")
def health_check():
    return Response(
        content="OK",
        status_code=200,
        headers={"Content-Type": "text/plain"}
    )
```

### Custom Status Codes

```python
@router.post("/items")
def create_item(item: Item):
    # Create item in database...

    return Response(
        content=item,
        status_code=201,  # Created
        headers={"Location": f"/items/{item.id}"}
    )

@router.delete("/items/{item_id}")
def delete_item(item_id: int):
    # Delete item...

    return Response(
        content=None,
        status_code=204  # No Content
    )
```

---

## RequestData

Internal unified request data container (used internally by FastOpenAPI).

```python
class RequestData:
    def __init__(
        self,
        path_params: dict[str, Any] = None,
        query_params: dict[str, Any] = None,
        headers: dict[str, str] = None,
        cookies: dict[str, str] = None,
        body: Any = None,
        form_data: dict[str, Any] = None,
        files: dict[str, FileUpload | list[FileUpload]] = None,
    )
```

### Attributes

- **path_params** (`dict[str, Any]`): URL path parameters
- **query_params** (`dict[str, Any]`): Query string parameters
- **headers** (`dict[str, str]`): HTTP headers
- **cookies** (`dict[str, str]`): HTTP cookies
- **body** (`Any`): Parsed JSON body
- **form_data** (`dict[str, Any]`): Form data
- **files** (`dict[str, FileUpload | list[FileUpload]]`): Uploaded files

**Note**: This class is used internally by FastOpenAPI for request data extraction. You typically don't need to use it directly in your application code.

---

## Common Type Patterns

### Optional Values

```python
from typing import Optional

@router.get("/items")
def get_item(
    item_id: int,
    include_details: Optional[bool] = Query(None)
):
    # include_details can be None, True, or False
    return {"item_id": item_id}
```

### Lists

```python
@router.get("/items")
def filter_items(
    tags: list[str] = Query([]),
    categories: list[int] = Query([])
):
    return {"tags": tags, "categories": categories}
```

### Union Types

```python
from typing import Union

@router.get("/search")
def search(
    query: Union[str, int] = Query(...)
):
    # query can be either string or int
    return {"query": query, "type": type(query).__name__}
```

### Pydantic Models

```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    username: str
    email: str

@router.post("/users")
def create_user(user: User = Body(...)):
    return user

@router.get("/users/{user_id}", response_model=User)
def get_user(user_id: int) -> User:
    return User(id=user_id, username="john", email="john@example.com")
```

---

## Type Validation

FastOpenAPI uses Pydantic for type validation:

### Automatic Conversion

```python
@router.get("/items")
def get_item(
    item_id: int = Query(...),  # "123" � 123
    price: float = Query(...),  # "19.99" � 19.99
    active: bool = Query(...)   # "true" � True
):
    return {
        "item_id": item_id,      # int
        "price": price,          # float
        "active": active         # bool
    }
```

### Complex Types

```python
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

@router.get("/events")
def get_events(
    start_date: date = Query(...),              # "2024-01-01"
    created_after: datetime = Query(...),       # "2024-01-01T10:00:00"
    event_id: UUID = Query(...),                # "550e8400-e29b-41d4-a716-446655440000"
    price: Decimal = Query(...)                 # "19.99"
):
    return {
        "start_date": start_date.isoformat(),
        "created_after": created_after.isoformat(),
        "event_id": str(event_id),
        "price": str(price)
    }
```

### Custom Validators

```python
from pydantic import BaseModel, field_validator

class CreateUser(BaseModel):
    username: str
    email: str
    age: int

    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v):
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        return v

    @field_validator('age')
    @classmethod
    def age_must_be_positive(cls, v):
        if v < 0:
            raise ValueError('Age must be positive')
        return v

@router.post("/users")
def create_user(user: CreateUser):
    return user
```

---

## See Also

- [Response Handling Guide](../guide/response_handling.md) - Working with responses
- [Request Body Guide](../guide/request_body.md) - Working with request bodies
- [File Upload Example](../examples/file_uploads.md) - File upload examples
- [Parameters Reference](parameters.md) - Parameter types
