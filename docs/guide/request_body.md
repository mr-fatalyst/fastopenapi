# Request Body

This guide covers handling request bodies including JSON, form data, and file uploads.

## JSON Request Body

The most common type of request body in REST APIs is JSON.

### Basic JSON Body

```python
from pydantic import BaseModel
from fastopenapi import Body

class Item(BaseModel):
    name: str
    price: float
    description: str | None = None

@router.post("/items")
def create_item(item: Item = Body(...)):
    return {"item": item}
```

**Request:**
```http
POST /items HTTP/1.1
Content-Type: application/json

{"name": "Laptop", "price": 999.99, "description": "Gaming laptop"}
```

### Automatic Body Detection

If a parameter is a Pydantic model, FastOpenAPI automatically treats it as the request body:

```python
@router.post("/items")
def create_item(item: Item):  # Automatically uses Body()
    return {"item": item}
```

### Nested Models

```python
class Address(BaseModel):
    street: str
    city: str
    country: str
    postal_code: str

class User(BaseModel):
    name: str
    email: str
    address: Address

@router.post("/users")
def create_user(user: User):
    return {"user": user}
```

**Request:**
```http
POST /users HTTP/1.1
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "address": {
    "street": "123 Main St",
    "city": "New York",
    "country": "USA",
    "postal_code": "10001"
  }
}
```

### Lists in Body

```python
@router.post("/items/bulk")
def create_items(items: list[Item]):
    return {"count": len(items), "items": items}
```

**Request:**
```http
POST /items/bulk HTTP/1.1
Content-Type: application/json

[
  {"name": "Item 1", "price": 10.0},
  {"name": "Item 2", "price": 20.0}
]
```

### Body with Path and Query Parameters

Combine body with other parameter types:

```python
@router.put("/items/{item_id}")
def update_item(
    item_id: int,                           # Path parameter
    item: Item,                             # Body
    notify: bool = Query(False)             # Query parameter
):
    return {
        "item_id": item_id,
        "item": item,
        "notify": notify
    }
```

**Request:**
```http
PUT /items/123?notify=true HTTP/1.1
Content-Type: application/json

{"name": "Updated Item", "price": 15.99}
```

## Form Data

Handle HTML form submissions and `application/x-www-form-urlencoded` data.

### Basic Form

```python
from fastopenapi import Form

@router.post("/login")
def login(
    username: str = Form(...),
    password: str = Form(...)
):
    # Authenticate user
    return {"username": username}
```

**Request:**
```http
POST /login HTTP/1.1
Content-Type: application/x-www-form-urlencoded

username=john&password=secret123
```

### Form with Pydantic Model

```python
class LoginForm(BaseModel):
    username: str
    password: str
    remember_me: bool = False

@router.post("/login")
def login(form: LoginForm = Form(...)):
    return {"username": form.username}
```

### Mixed Form and Query Parameters

```python
@router.post("/search")
def search(
    query: str = Form(...),
    page: int = Query(1),
    per_page: int = Query(10)
):
    return {
        "query": query,
        "page": page,
        "per_page": per_page
    }
```

## File Uploads

Handle single and multiple file uploads.

### Single File Upload

```python
from fastopenapi import File, FileUpload

@router.post("/upload")
async def upload_file(
    file: FileUpload = File(...)
):
    content = await file.aread()  # For async frameworks
    # or: content = file.read()   # For sync frameworks
    
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(content)
    }
```

**Request:**
```http
POST /upload HTTP/1.1
Content-Type: multipart/form-data; boundary=----Boundary

------Boundary
Content-Disposition: form-data; name="file"; filename="document.pdf"
Content-Type: application/pdf

[binary content]
------Boundary--
```

### FileUpload Object

The `FileUpload` object provides:

- `filename: str` - Original filename
- `content_type: str` - MIME type
- `size: int | None` - File size in bytes
- `file: Any` - Framework-specific file object
- `read()` - Read file content (sync)
- `aread()` - Read file content (async)

### Multiple File Uploads

```python
@router.post("/upload-multiple")
async def upload_files(
    files: list[FileUpload] = File(...)
):
    results = []
    for file in files:
        content = await file.aread()
        results.append({
            "filename": file.filename,
            "size": len(content)
        })
    return {"files": results}
```

### File with Additional Form Data

```python
@router.post("/upload-with-data")
async def upload_with_data(
    file: FileUpload = File(...),
    title: str = Form(...),
    description: str = Form(None)
):
    content = await file.aread()
    return {
        "filename": file.filename,
        "title": title,
        "description": description,
        "size": len(content)
    }
```

### Optional File Upload

```python
@router.post("/profile")
async def update_profile(
    name: str = Form(...),
    avatar: FileUpload | None = File(None)
):
    if avatar:
        content = await avatar.aread()
        # Save avatar
        return {"name": name, "avatar_uploaded": True}
    return {"name": name, "avatar_uploaded": False}
```

### File Validation

```python
from fastopenapi.errors import BadRequestError

@router.post("/upload")
async def upload_file(file: FileUpload = File(...)):
    # Check file size
    if file.size and file.size > 10 * 1024 * 1024:  # 10 MB
        raise BadRequestError("File too large (max 10 MB)")
    
    # Check file type
    allowed_types = ["image/jpeg", "image/png", "image/gif"]
    if file.content_type not in allowed_types:
        raise BadRequestError(f"Invalid file type: {file.content_type}")
    
    content = await file.aread()
    # Process file
    return {"filename": file.filename, "size": len(content)}
```

### Saving Files

```python
import os
from pathlib import Path

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/upload")
async def upload_file(file: FileUpload = File(...)):
    content = await file.aread()
    
    # Generate safe filename
    safe_filename = file.filename.replace("/", "_")
    file_path = UPLOAD_DIR / safe_filename
    
    # Save to disk
    with open(file_path, "wb") as f:
        f.write(content)
    
    return {
        "filename": file.filename,
        "saved_as": str(file_path),
        "size": len(content)
    }
```

### Streaming Large Files

For large files, read in chunks:

```python
@router.post("/upload-large")
async def upload_large_file(file: FileUpload = File(...)):
    file_path = UPLOAD_DIR / file.filename
    
    # For async frameworks
    with open(file_path, "wb") as f:
        # Read in chunks
        content = await file.aread()
        f.write(content)
    
    return {
        "filename": file.filename,
        "size": file_path.stat().st_size
    }
```

## Body Validation

### Required Fields

```python
class User(BaseModel):
    name: str                    # Required
    email: str                   # Required
    age: int | None = None       # Optional
```

### Field Constraints

```python
from pydantic import Field

class Item(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0, description="Price must be positive")
    quantity: int = Field(1, ge=1, le=1000)
    tags: list[str] = Field(default_factory=list, max_length=10)
```

### Custom Validators

```python
from pydantic import field_validator

class User(BaseModel):
    username: str
    password: str
    
    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v):
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        return v
    
    @field_validator('password')
    @classmethod
    def password_strong(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v
```

### Complex Validation

```python
from pydantic import model_validator

class DateRange(BaseModel):
    start_date: date
    end_date: date
    
    @model_validator(mode='after')
    def check_dates(self):
        if self.start_date > self.end_date:
            raise ValueError('start_date must be before end_date')
        return self
```

## Response Examples

### Successful Creation

```python
@router.post("/items", status_code=201)
def create_item(item: Item):
    # Save to database
    item_dict = item.model_dump()
    item_dict["id"] = generate_id()
    return item_dict
```

**Response:**
```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "id": 123,
  "name": "Laptop",
  "price": 999.99,
  "description": null
}
```

### Validation Error

**Request:**
```http
POST /items HTTP/1.1
Content-Type: application/json

{"name": "Item", "price": -10}
```

**Response:**
```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json

{
  "error": {
    "type": "validation_error",
    "message": "Validation error for parameter 'price'",
    "status": 422,
    "details": "Input should be greater than 0"
  }
}
```

## Sync vs Async File Handling

### Synchronous (Flask, Django WSGI)

```python
@router.post("/upload")
def upload_file(file: FileUpload = File(...)):
    content = file.read()  # Sync read
    return {"size": len(content)}
```

### Asynchronous (Starlette, AIOHTTP, Sanic)

```python
@router.post("/upload")
async def upload_file(file: FileUpload = File(...)):
    content = await file.aread()  # Async read
    return {"size": len(content)}
```

## Best Practices

### 1. Use Pydantic Models

```python
# Good - type-safe and validated
class CreateItemRequest(BaseModel):
    name: str
    price: float

@router.post("/items")
def create_item(request: CreateItemRequest):
    pass

# Avoid - no validation
@router.post("/items")
def create_item(data: dict):
    pass
```

### 2. Validate File Uploads

```python
# Good - validate before processing
@router.post("/upload")
async def upload(file: FileUpload = File(...)):
    if file.size > MAX_SIZE:
        raise BadRequestError("File too large")
    if not file.content_type.startswith("image/"):
        raise BadRequestError("Only images allowed")
    # Process file
```

### 3. Use Descriptive Field Names

```python
# Good
class CreateUserRequest(BaseModel):
    full_name: str
    email_address: str
    phone_number: str | None

# Avoid
class CreateUserRequest(BaseModel):
    n: str
    e: str
    p: str | None
```

### 4. Provide Default Values

```python
# Good
class SearchRequest(BaseModel):
    query: str
    page: int = 1
    per_page: int = 20
    sort_by: str = "created_at"
```

### 5. Document Your Models

```python
class Item(BaseModel):
    """Represents an item in the store."""
    
    name: str = Field(..., description="The item name", example="Laptop")
    price: float = Field(..., description="Price in USD", example=999.99)
    in_stock: bool = Field(True, description="Availability status")
```

## Common Patterns

### Create/Update Split

```python
class ItemCreate(BaseModel):
    name: str
    price: float
    description: str | None = None

class ItemUpdate(BaseModel):
    name: str | None = None
    price: float | None = None
    description: str | None = None

@router.post("/items")
def create_item(item: ItemCreate):
    # All fields required
    return item

@router.patch("/items/{item_id}")
def update_item(item_id: int, updates: ItemUpdate):
    # All fields optional
    return {"item_id": item_id, "updates": updates}
```

### Bulk Operations

```python
class BulkCreateRequest(BaseModel):
    items: list[ItemCreate] = Field(..., max_length=100)

@router.post("/items/bulk")
def bulk_create(request: BulkCreateRequest):
    return {"count": len(request.items)}
```

## Next Steps

- [Response Handling](response_handling.md) - Customize response format
- [Validation](validation.md) - Advanced Pydantic validation
- [Error Handling](error_handling.md) - Handle validation errors
- [Dependencies](dependencies.md) - Inject dependencies into endpoints
