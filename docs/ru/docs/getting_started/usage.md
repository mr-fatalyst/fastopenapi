# Использование

В этом разделе описано, как использовать FastOpenAPI для документирования и валидации конечных точек вашего API. Ниже представлены отдельные примеры для каждого сценария использования, включая обработку исключений библиотеки и самого фреймворка.

---

## Определение маршрутов

### Доступные методы

- `@router.get(path, response_errors, response_model, tags, status_code)`
- `@router.post(path, response_errors, response_model, tags, status_code)`
- `@router.patch(path, response_errors, response_model, tags, status_code)`
- `@router.put(path, response_errors, response_model, tags, status_code)`
- `@router.delete(path, response_errors, response_model, tags, status_code)`

#### Краткое описание

- `path` — URL метода.
- `response_errors` — список кодов ошибок, которые может вернуть метод.
- `response_model` — ваша Pydantic-модель. Также можно использовать int, float, str, bool.
- `tags` — OpenAPI-теги для обработчика.
- `status_code` — код ответа при успехе.

### Примеры

```python
from pydantic import BaseModel
from typing import Optional

# Не используйте этот роутер напрямую. Это просто пример.
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
    data = {}
    return UserResponse(**data)

@router.post("/user", tags=["User"], status_code=201, response_model=UserResponse)
def create_user(user_data: CreateUserRequest):
    data = {}
    return UserResponse(**data)

@router.patch("/user/{user_id}", tags=["User"], status_code=200, response_model=UserResponse)
def update_user(user_id: int, user_data: UpdateUserRequest):
    data = {}
    return UserResponse(**data)

@router.delete("/user/{user_id}", tags=["User"], status_code=204)
def delete_user(user_id: int):
    return None
```

## Простой запрос (список элементов)

```python
@router.get("/items")
async def list_items():
    return {"items": ["foo", "bar"]}
```

## Параметр в пути

```python
@router.get("/items/{item_id}")
async def get_item(item_id: int):
    item = database.get(item_id)
    if item is None:
        raise ResourceNotFoundError(f"Item {item_id} not found")
    return item
```

---

## Обработка query-параметров

```python
@router.get("/search")
async def search(q: str = "", limit: int = 10):
    if limit < 0:
        raise BadRequestError("Limit must be non-negative")
    return {"query": q, "limit": limit}
```

---

## Обработка тела запроса через Pydantic

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

## Структурирование кода с подроутерами

**Файл: users.py**
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

**Файл: main.py**
```python
from fastopenapi.routers import StarletteRouter
from starlette.applications import Starlette
from users import user_router

app = Starlette()
main_router = StarletteRouter(app=app)
main_router.include_router(user_router, prefix="/v1")
```

---

## Обработка ошибок

### Исключения библиотеки

```python
from fastopenapi.error_handler import ResourceNotFoundError

@router.get("/products/{product_id}")
async def get_product(product_id: int):
    product = database.get_product(product_id)
    if product is None:
        raise ResourceNotFoundError(f"Product {product_id} not found")
    return product
```

### Исключения фреймворка

#### Flask

```python
from flask import abort

@router.get("/orders/{order_id}")
def get_order(order_id: int):
    order = get_order_from_db(order_id)
    if order is None:
        abort(404, description="Order not found")
    return order
```

#### Falcon

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

Эти примеры показывают, как:

- Определять маршруты с параметрами пути, query и телом запроса;
- Использовать Pydantic для валидации и генерации схем;
- Обрабатывать ошибки через встроенные исключения и исключения фреймворков.

---

## Примеры проектов

Смотрите примеры для каждого поддерживаемого фреймворка в директории [`examples/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples) репозитория.

---
