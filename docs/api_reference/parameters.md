# Parameters API Reference

Complete reference for all parameter classes in FastOpenAPI.

## Query

Extract and validate query parameters from the URL query string.

```python
from fastopenapi import Query
```

### Signature

```python
Query(
    default: Any = None,
    *,
    alias: str | None = None,
    title: str | None = None,
    description: str | None = None,
    gt: float | None = None,
    ge: float | None = None,
    lt: float | None = None,
    le: float | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    pattern: str | None = None,
    strict: bool | None = None,
    multiple_of: float | None = None,
    allow_inf_nan: bool | None = None,
    max_digits: int | None = None,
    decimal_places: int | None = None,
    examples: list[Any] | None = None,
    deprecated: bool | None = None,
    include_in_schema: bool = True,
    json_schema_extra: dict[str, Any] | None = None,
)
```

### Parameters

- **default**: Default value if not provided (default: `None`)
- **alias**: Alternative name in the query string
- **title**: Title for OpenAPI documentation
- **description**: Description for OpenAPI documentation
- **gt**: Greater than validation (numbers)
- **ge**: Greater than or equal validation (numbers)
- **lt**: Less than validation (numbers)
- **le**: Less than or equal validation (numbers)
- **min_length**: Minimum length (strings/arrays)
- **max_length**: Maximum length (strings/arrays)
- **pattern**: Regular expression pattern (strings)
- **strict**: Enable strict type checking
- **multiple_of**: Number must be a multiple of this value
- **allow_inf_nan**: Allow infinity and NaN values
- **max_digits**: Maximum number of digits
- **decimal_places**: Maximum decimal places
- **examples**: Example values for documentation
- **deprecated**: Mark as deprecated in docs
- **include_in_schema**: Include in OpenAPI schema
- **json_schema_extra**: Extra JSON schema properties

### Example

```python
@router.get("/items")
def list_items(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search query"),
):
    return {"page": page, "per_page": per_page}
```

---

## Path

Extract and validate path parameters from the URL path.

```python
from fastopenapi import Path
```

### Signature

```python
Path(
    default: Any = ...,  # Always required (...)
    *,
    alias: str | None = None,
    title: str | None = None,
    description: str | None = None,
    gt: float | None = None,
    ge: float | None = None,
    lt: float | None = None,
    le: float | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    pattern: str | None = None,
    strict: bool | None = None,
    multiple_of: float | None = None,
    allow_inf_nan: bool | None = None,
    max_digits: int | None = None,
    decimal_places: int | None = None,
    examples: list[Any] | None = None,
    deprecated: bool | None = None,
    include_in_schema: bool = True,
    json_schema_extra: dict[str, Any] | None = None,
)
```

### Parameters

Same as `Query`, except:

- **default**: Must be `...` (ellipsis) - path parameters are always required

### Important

Path parameters **cannot** have default values. Attempting to provide a default value other than `...` will raise a `ValueError`.

### Example

```python
@router.get("/users/{user_id}/posts/{post_id}")
def get_post(
    user_id: int = Path(..., ge=1, description="User ID"),
    post_id: int = Path(..., ge=1, description="Post ID"),
):
    return {"user_id": user_id, "post_id": post_id}
```

---

## Header

Extract and validate HTTP header values.

```python
from fastopenapi import Header
```

### Signature

```python
Header(
    default: Any = None,
    *,
    alias: str | None = None,
    convert_underscores: bool = True,
    title: str | None = None,
    description: str | None = None,
    gt: float | None = None,
    ge: float | None = None,
    lt: float | None = None,
    le: float | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    pattern: str | None = None,
    strict: bool | None = None,
    multiple_of: float | None = None,
    allow_inf_nan: bool | None = None,
    max_digits: int | None = None,
    decimal_places: int | None = None,
    examples: list[Any] | None = None,
    deprecated: bool | None = None,
    include_in_schema: bool = True,
    json_schema_extra: dict[str, Any] | None = None,
)
```

### Parameters

Same as `Query`, plus:

- **convert_underscores**: Automatically convert underscores to hyphens (default: `True`)

### Example

```python
@router.get("/items")
def list_items(
    user_agent: str | None = Header(None, alias="User-Agent"),
    api_key: str = Header(..., alias="X-API-Key", description="API Key"),
):
    return {"user_agent": user_agent}
```

**Note**: HTTP headers are case-insensitive but typically use kebab-case (e.g., `User-Agent`, `X-API-Key`).

---

## Cookie

Extract and validate HTTP cookie values.

```python
from fastopenapi import Cookie
```

### Signature

```python
Cookie(
    default: Any = None,
    *,
    alias: str | None = None,
    title: str | None = None,
    description: str | None = None,
    gt: float | None = None,
    ge: float | None = None,
    lt: float | None = None,
    le: float | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    pattern: str | None = None,
    strict: bool | None = None,
    multiple_of: float | None = None,
    allow_inf_nan: bool | None = None,
    max_digits: int | None = None,
    decimal_places: int | None = None,
    examples: list[Any] | None = None,
    deprecated: bool | None = None,
    include_in_schema: bool = True,
    json_schema_extra: dict[str, Any] | None = None,
)
```

### Parameters

Same as `Query`.

### Example

```python
@router.get("/profile")
def get_profile(
    session_id: str = Cookie(..., description="Session ID"),
    preferences: str | None = Cookie(None),
):
    return {"session_id": session_id}
```

---

## Body

Extract and validate JSON request body.

```python
from fastopenapi import Body
```

### Signature

```python
Body(
    default: Any = None,
    *,
    embed: bool | None = None,
    media_type: str = "application/json",
    alias: str | None = None,
    title: str | None = None,
    description: str | None = None,
    gt: float | None = None,
    ge: float | None = None,
    lt: float | None = None,
    le: float | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    pattern: str | None = None,
    strict: bool | None = None,
    multiple_of: float | None = None,
    allow_inf_nan: bool | None = None,
    max_digits: int | None = None,
    decimal_places: int | None = None,
    examples: list[Any] | None = None,
    deprecated: bool | None = None,
    include_in_schema: bool = True,
    json_schema_extra: dict[str, Any] | None = None,
)
```

### Parameters

Same as `Query`, plus:

- **embed**: Embed the body in a field (for multiple body parameters)
- **media_type**: MIME type of the body (default: `"application/json"`)

### Example

```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float

@router.post("/items")
def create_item(item: Item = Body(...)):
    return item
```

---

## Form

Extract and validate form data from `application/x-www-form-urlencoded` requests.

```python
from fastopenapi import Form
```

### Signature

```python
Form(
    default: Any = None,
    *,
    media_type: str = "application/x-www-form-urlencoded",
    alias: str | None = None,
    title: str | None = None,
    description: str | None = None,
    gt: float | None = None,
    ge: float | None = None,
    lt: float | None = None,
    le: float | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    pattern: str | None = None,
    strict: bool | None = None,
    multiple_of: float | None = None,
    allow_inf_nan: bool | None = None,
    max_digits: int | None = None,
    decimal_places: int | None = None,
    examples: list[Any] | None = None,
    deprecated: bool | None = None,
    include_in_schema: bool = True,
    json_schema_extra: dict[str, Any] | None = None,
)
```

### Parameters

Same as `Body`.

### Example

```python
@router.post("/login")
def login(
    username: str = Form(...),
    password: str = Form(...),
):
    return {"username": username}
```

---

## File

Handle file uploads from `multipart/form-data` requests.

```python
from fastopenapi import File
```

### Signature

```python
File(
    default: Any = None,
    *,
    media_type: str = "multipart/form-data",
    alias: str | None = None,
    title: str | None = None,
    description: str | None = None,
    examples: list[Any] | None = None,
    deprecated: bool | None = None,
    include_in_schema: bool = True,
    json_schema_extra: dict[str, Any] | None = None,
)
```

### Parameters

Same as `Form` (inherits from `Form`, validation constraints don't apply to files).

### Example

```python
from fastopenapi import File, FileUpload

@router.post("/upload")
def upload_file(file: FileUpload = File(...)):
    content = file.read()  # Sync frameworks
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": file.size
    }

@router.post("/upload-async")
async def upload_file_async(file: FileUpload = File(...)):
    content = await file.aread()  # Async frameworks
    return {"filename": file.filename}
```

---

## Pre-defined Types

FastOpenAPI provides pre-defined annotated types for common patterns:

### Validation Types

```python
from fastopenapi import (
    PositiveInt,      # int with gt=0
    NonNegativeInt,   # int with ge=0
    PositiveFloat,    # float with gt=0.0
    NonEmptyStr,      # str with min_length=1
    LimitedStr,       # str with min_length=1, max_length=255
)

@router.get("/items")
def list_items(
    page: PositiveInt,
    limit: NonNegativeInt = Query(10),
):
    return {"page": page, "limit": limit}
```

### ID Patterns

```python
from fastopenapi import UserId, ItemId

@router.get("/users/{user_id}")
def get_user(user_id: UserId):  # int >= 1
    return {"user_id": user_id}

@router.get("/items/{item_id}")
def get_item(item_id: ItemId):  # int >= 1
    return {"item_id": item_id}
```

### Pagination Patterns

```python
from fastopenapi import PageQuery, LimitQuery, OffsetQuery

@router.get("/items")
def list_items(
    page: PageQuery = Query(1),        # ge=1
    limit: LimitQuery = Query(10),     # ge=1, le=100
    offset: OffsetQuery = Query(0),    # ge=0
):
    return {"page": page, "limit": limit, "offset": offset}
```

---

## Validation Constraints

All parameter classes support Pydantic validation constraints:

### Numeric Constraints

- **gt**: Greater than
- **ge**: Greater than or equal
- **lt**: Less than
- **le**: Less than or equal
- **multiple_of**: Must be a multiple of this value

```python
age: int = Query(..., ge=0, le=150)
price: float = Query(..., gt=0, le=1000000)
quantity: int = Query(..., multiple_of=10)
```

### String Constraints

- **min_length**: Minimum string length
- **max_length**: Maximum string length
- **pattern**: Regular expression pattern

```python
username: str = Query(..., min_length=3, max_length=50)
email: str = Query(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
```

### Number Constraints

- **max_digits**: Maximum total digits
- **decimal_places**: Maximum decimal places
- **allow_inf_nan**: Allow infinity and NaN

```python
price: float = Query(..., max_digits=10, decimal_places=2)
```

---

## Metadata

All parameters support OpenAPI metadata:

```python
@router.get("/items")
def list_items(
    search: str = Query(
        None,
        title="Search Query",
        description="Search items by name or description",
        examples=["laptop", "phone"],
        deprecated=False,
        alias="q"
    )
):
    return {}
```

- **title**: Short title for the parameter
- **description**: Longer description
- **examples**: Example values (shown in OpenAPI docs)
- **deprecated**: Mark parameter as deprecated
- **alias**: Alternative parameter name
- **include_in_schema**: Include in OpenAPI schema (default: `True`)
- **json_schema_extra**: Additional JSON schema properties

---

## See Also

- [Request Parameters Guide](../guide/request_parameters.md) - Usage examples
- [Validation Guide](../guide/validation.md) - Validation patterns
- [Types Reference](types.md) - Core type definitions
