# Verwendung

In diesem Abschnitt wird erklärt, wie FastOpenAPI genutzt wird, um API-Endpunkte zu dokumentieren und Eingaben/Ausgaben zu validieren. Es folgen Beispiele für verschiedene Anwendungsszenarien, inklusive Fehlerbehandlung durch die Bibliothek und durch das zugrundeliegende Framework.

---

## Definition von Endpunkten

### Verfügbare Methoden

- `@router.get(path, response_errors, response_model, tags, status_code)`
- `@router.post(path, response_errors, response_model, tags, status_code)`
- `@router.patch(path, response_errors, response_model, tags, status_code)`
- `@router.put(path, response_errors, response_model, tags, status_code)`
- `@router.delete(path, response_errors, response_model, tags, status_code)`

#### Kurzbeschreibung

- `path` – die URL des Endpunkts.
- `response_errors` – Liste möglicher Fehlerstatuscodes für die OpenAPI-Spezifikation.
- `response_model` – Pydantic-Modell oder einfacher Python-Typ für das Antwortschema.
- `tags` – OpenAPI-Tags zur Gruppierung.
- `status_code` – HTTP-Statuscode bei erfolgreicher Antwort.

### Beispiel

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

## Einfacher GET-Endpunkt

```python
@router.get("/items")
async def list_items():
    return {"items": ["foo", "bar"]}
```

## Pfadparameter

```python
@router.get("/items/{item_id}")
async def get_item(item_id: int):
    item = database.get(item_id)
    if item is None:
        raise ResourceNotFoundError(f"Item {item_id} nicht gefunden")
    return item
```

## Query-Parameter

```python
@router.get("/search")
async def search(q: str = "", limit: int = 10):
    if limit < 0:
        raise BadRequestError("Limit darf nicht negativ sein")
    return {"query": q, "limit": limit}
```

## Anfragekörper mit Pydantic validieren

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
    except DatabaseError:
        abort(500, description="Datenbankfehler")
    return item
```

## Router aufteilen mit Subroutern

**Datei: users.py**
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

**Datei: main.py**
```python
from fastopenapi.routers import StarletteRouter
from starlette.applications import Starlette
from users import user_router

app = Starlette()
main_router = StarletteRouter(app=app)
main_router.include_router(user_router, prefix="/v1")
```

## Fehlerbehandlung

### Bibliothekseigene Fehler

```python
from fastopenapi.error_handler import ResourceNotFoundError

@router.get("/products/{product_id}")
async def get_product(product_id: int):
    product = database.get_product(product_id)
    if product is None:
        raise ResourceNotFoundError(f"Produkt {product_id} nicht gefunden")
    return product
```

### Framework-Fehler

#### Flask

```python
from flask import abort

@router.get("/orders/{order_id}")
def get_order(order_id: int):
    order = get_order_from_db(order_id)
    if order is None:
        abort(404, description="Bestellung nicht gefunden")
    return order
```

#### Falcon

```python
import falcon

@router.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: int):
    invoice = database.get_invoice(invoice_id)
    if invoice is None:
        raise falcon.HTTPNotFound(title="Nicht gefunden", description="Rechnung nicht gefunden")
    return invoice
```

---

Diese Beispiele zeigen, wie man:

- Pfad-, Query- und Body-Parameter definiert,
- Pydantic zur Validierung und OpenAPI-Generierung nutzt,
- Fehler über Ausnahmen behandelt (sowohl mitgeliefert als auch framework-spezifisch).

## Projektbeispiele

Siehe das Verzeichnis [`examples/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples) im Repository für vollständige Beispiele je Framework.
