# Usage

This section explains how to use FastOpenAPI to document and validate your API endpoints. Below you will find separate examples for each usage scenario, including handling of both library and framework exceptions.

---

## Defining Endpoints

### Available methods

- `@router.get(path, response_errors, response_model, tags, status_code)`
- `@router.post(path, response_errors, response_model, tags, status_code)`
- `@router.patch(path, response_errors, response_model, tags, status_code)`
- `@router.put(path, response_errors, response_model, tags, status_code)`
- `@router.delete(path, response_errors, response_model, tags, status_code)`

#### Short descriptions

- `path` - the method URL.
- `response_errors` - the list of error codes for your method.
- `response_model` - your Pydantic model. You can use int, float, str, bool as well.
- `tags` - OpenAPI tags for your handler.
- `status_code` - the success response code.

### Examples for methods
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

## Basic request (Listing Items)

```python
@router.get("/items")
async def list_items():
    return {"items": ["foo", "bar"]}
```

## Request with Path Parameter

```python
@router.get("/items/{item_id}")
async def get_item(item_id: int):
    item = database.get(item_id)
    if item is None:
        # You can use framework-specific exception here 
        raise ResourceNotFoundError(f"Item {item_id} not found")
    return item
```

---

## Handling Query Parameters

```python
@router.get("/search")
async def search(q: str = "", limit: int = 10):
    if limit < 0:
        # You can use framework-specific exception here 
        raise BadRequestError("Limit must be non-negative")
    return {"query": q, "limit": limit}
```

---

## Handling Request Bodies with Pydantic Models

```python
from flask import abort
from pydantic import BaseModel


class Item(BaseModel):
    name: str
    price: float

@router.post("/items", response_model=Item, status_code=201)
def create_item(item: Item):
    try:
        save_to_database(item)
    except DatabaseError as e:
        abort(500, description="Database error")
    return item
```

---

## Organizing Code with Sub-Routers

**File: users.py**
```python
from fastopenapi.routers import StarletteRouter
from pydantic import BaseModel
from typing import List

user_router = StarletteRouter()

class User(BaseModel):
    id: int
    name: str

@user_router.get("/users", response_model=List[User])
async def list_users():
    return [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

@user_router.post("/users", response_model=User, status_code=201)
async def create_user(user: User):
    save_user_to_database(user)
    return user
```

**File: main.py**
```python
from fastopenapi.routers import StarletteRouter
from starlette.applications import Starlette
from users import user_router

app = Starlette()
main_router = StarletteRouter(app=app)
main_router.include_router(user_router, prefix="/v1")
```

---

## Exception Handling Examples

### Library Exceptions

```python
from fastopenapi.error_handler import ResourceNotFoundError

@router.get("/products/{product_id}")
async def get_product(product_id: int):
    product = database.get_product(product_id)
    if product is None:
        # You can use framework-specific exception here 
        raise ResourceNotFoundError(f"Product {product_id} not found")
    return product
```

### Framework-Specific Exceptions

#### Flask Example

```python
from flask import abort

@router.get("/orders/{order_id}")
def get_order(order_id: int):
    order = get_order_from_db(order_id)
    if order is None:
        abort(404, description="Order not found")
    return order
```

#### Falcon Example

```python
import falcon

@router.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: int):
    invoice = database.get_invoice(invoice_id)
    if invoice is None:
        raise falcon.HTTPNotFound(title="Not Found", description="Invoice not found")
    return invoice
```

---

These examples demonstrate how you can:

- Define routes with various parameter types (path, query, body);
- Use Pydantic for request and response validation and automatic OpenAPI schema generation;
- Handle errors using both FastOpenAPI's built-in exception classes and framework-specific exceptions.

---

## Project Examples


See examples for each supported framework in the [`examples/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples) directory of the repository.

---
