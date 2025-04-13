# Uso

En esta sección se explica cómo usar FastOpenAPI para documentar rutas de API y validar entradas/salidas. Se incluyen ejemplos para distintos escenarios, incluida la gestión de errores tanto con la biblioteca como con el framework subyacente.

---

## Definición de rutas

### Métodos disponibles

- `@router.get(path, response_errors, response_model, tags, status_code)`
- `@router.post(path, response_errors, response_model, tags, status_code)`
- `@router.patch(path, response_errors, response_model, tags, status_code)`
- `@router.put(path, response_errors, response_model, tags, status_code)`
- `@router.delete(path, response_errors, response_model, tags, status_code)`

#### Descripción rápida

- `path` – ruta de la API.
- `response_errors` – lista de posibles códigos de error para OpenAPI.
- `response_model` – modelo Pydantic o tipo simple (str, int, etc.) para validar la respuesta.
- `tags` – etiquetas OpenAPI para agrupar rutas.
- `status_code` – código de estado HTTP por defecto.

---

## Ejemplo básico

```python
from pydantic import BaseModel
from typing import Optional
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

---

## Parámetros de ruta

```python
@router.get("/items/{item_id}")
async def get_item(item_id: int):
    item = database.get(item_id)
    if item is None:
        raise ResourceNotFoundError(f"Ítem {item_id} no encontrado")
    return item
```

## Parámetros de consulta (query)

```python
@router.get("/search")
async def search(q: str = "", limit: int = 10):
    if limit < 0:
        raise BadRequestError("El límite no puede ser negativo")
    return {"query": q, "limit": limit}
```

## Validación con modelos Pydantic (cuerpo de la solicitud)

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
        abort(500, description="Error en base de datos")
    return item
```

---

## Subrouters (modularización)

**Archivo: users.py**

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
```

**Archivo: main.py**

```python
from fastopenapi.routers import StarletteRouter
from starlette.applications import Starlette
from users import user_router

app = Starlette()
main_router = StarletteRouter(app=app)
main_router.include_router(user_router, prefix="/v1")
```

---

## Manejo de errores

### Errores internos de FastOpenAPI

```python
from fastopenapi.error_handler import ResourceNotFoundError

@router.get("/products/{product_id}")
async def get_product(product_id: int):
    product = db.get(product_id)
    if product is None:
        raise ResourceNotFoundError(f"Producto {product_id} no encontrado")
    return product
```

### Errores específicos del framework

#### Flask

```python
from flask import abort

@router.get("/orders/{order_id}")
def get_order(order_id: int):
    order = get_order_from_db(order_id)
    if order is None:
        abort(404, description="Orden no encontrada")
    return order
```

#### Falcon

```python
import falcon

@router.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: int):
    invoice = db.get(invoice_id)
    if invoice is None:
        raise falcon.HTTPNotFound(title="No encontrado", description="Factura no encontrada")
    return invoice
```

---

## Ejemplos completos

Consulta el directorio [`examples/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples) para ver implementaciones funcionales por framework.
