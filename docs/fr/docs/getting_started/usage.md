# Utilisation

Cette section explique comment utiliser FastOpenAPI pour documenter et valider les routes de votre API. Elle comprend des exemples concrets pour la gestion des entrées/sorties, des erreurs et l'organisation modulaire du code.

---

## Définition de routes

### Méthodes disponibles

- `@router.get(path, response_model, tags, status_code, response_errors)`
- `@router.post(...)`
- `@router.put(...)`
- `@router.patch(...)`
- `@router.delete(...)`

#### Options courantes

- `response_model`: modèle Pydantic attendu en sortie
- `tags`: liste de catégories OpenAPI
- `status_code`: code de réponse par défaut
- `response_errors`: dictionnaire des erreurs possibles

---

## Exemple de base

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

## Paramètres de route

```python
@router.get("/items/{item_id}")
async def get_item(item_id: int):
    item = database.get(item_id)
    if item is None:
        raise ResourceNotFoundError(f"Item {item_id} introuvable")
    return item
```

## Paramètres de requête

```python
@router.get("/search")
async def search(q: str = "", limit: int = 10):
    if limit < 0:
        raise BadRequestError("La limite doit être positive")
    return {"query": q, "limit": limit}
```

## Corps de requête avec Pydantic

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
        abort(500, description="Erreur interne")
    return item
```

---

## Utilisation de sous-routeurs

**users.py**

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

**main.py**

```python
from fastopenapi.routers import StarletteRouter
from starlette.applications import Starlette
from users import user_router

app = Starlette()
main_router = StarletteRouter(app=app)
main_router.include_router(user_router, prefix="/v1")
```

---

## Gestion des erreurs

### Erreurs FastOpenAPI

```python
from fastopenapi.error_handler import ResourceNotFoundError

@router.get("/products/{product_id}")
async def get_product(product_id: int):
    product = db.get(product_id)
    if product is None:
        raise ResourceNotFoundError(f"Produit {product_id} non trouvé")
    return product
```

### Erreurs spécifiques au framework

#### Flask

```python
from flask import abort

@router.get("/orders/{order_id}")
def get_order(order_id: int):
    order = get_order_from_db(order_id)
    if order is None:
        abort(404, description="Commande non trouvée")
    return order
```

#### Falcon

```python
import falcon

@router.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: int):
    invoice = db.get(invoice_id)
    if invoice is None:
        raise falcon.HTTPNotFound(title="Non trouvé", description="Facture introuvable")
    return invoice
```

---

## Exemples complets

Consultez le répertoire [`examples/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples) pour des projets complets utilisant différents frameworks.
