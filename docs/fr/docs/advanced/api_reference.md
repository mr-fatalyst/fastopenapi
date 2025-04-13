# Référence API

Cette section fournit une référence détaillée des classes et modules de FastOpenAPI, incluant les interfaces, méthodes et exemples d’utilisation.

## Structure des fichiers

FastOpenAPI suit une architecture modulaire :

```
fastopenapi/
├── base_router.py
└── routers/
    ├── aiohttp.py
    ├── falcon.py
    ├── flask.py
    ├── quart.py
    ├── sanic.py
    ├── starlette.py
    └── tornado.py
```

---

## BaseRouter

**Description :** Classe de base abstraite fournissant les fonctionnalités communes de routage et de génération de schéma OpenAPI. Toutes les implémentations de frameworks héritent de cette classe.

### Méthodes principales

- `__init__(app)`: initialise avec l’application du framework.
- `get(path, **options)`, `post(...)`, `put(...)`, `patch(...)`, `delete(...)` : enregistrent les routes HTTP correspondantes.
- `include_router(router, prefix="")`: permet l’inclusion de sous-routeurs avec un préfixe.
- `generate_openapi_schema()`: génère dynamiquement le schéma OpenAPI.
- `get_openapi_schema()`: renvoie le schéma OpenAPI mis en cache.

### Attributs

- `app`: instance de l’application framework.
- `routes`: liste interne des routes définies.
- `docs_url`, `redoc_url`, `openapi_url`: chemins pour la documentation interactive.
- `title`, `version`, `description`: métadonnées du schéma.

---

## Routeurs spécifiques aux frameworks

FastOpenAPI fournit un routeur dédié pour chaque framework pris en charge :

- `AioHttpRouter`
- `FalconRouter`
- `FlaskRouter`
- `QuartRouter`
- `SanicRouter`
- `StarletteRouter`
- `TornadoRouter`

Tous ces routeurs héritent de `BaseRouter` et adaptent la logique de routing à l’interface du framework.

---

## Exemple de sous-routeur

```python
api_v1 = FlaskRouter()

@api_v1.get("/users")
def users():
    return [{"name": "Alice"}, {"name": "Bob"}]

main_router = FlaskRouter(app=app)
main_router.include_router(api_v1, prefix="/v1")
```

---

## Gestion des erreurs

### Erreurs personnalisées FastOpenAPI

```python
from fastopenapi.error_handler import BadRequestError, ResourceNotFoundError

@router.get("/validate")
def validate_input(param: int):
    if param < 0:
        raise BadRequestError("Le paramètre doit être positif")

@router.get("/items/{item_id}")
def get_item(item_id: int):
    item = db.get(item_id)
    if item is None:
        raise ResourceNotFoundError(f"Élément {item_id} introuvable")
```

### Compatibilité avec les erreurs natives du framework

#### AioHTTP

```python
from aiohttp import web

@router.get("/notfound")
def aiohttp_notfound():
    raise web.HTTPNotFound(reason="Not Found")
```

#### Falcon

```python
import falcon

@router.get("/notfound")
async def falcon_notfound():
    raise falcon.HTTPNotFound(title="Not Found", description="Falcon error")
```

#### Flask

```python
from flask import abort

@router.get("/notfound")
def flask_notfound():
    abort(404, description="Flask error")
```

#### Quart

```python
from quart import abort

@router.get("/notfound")
async def quart_notfound():
    abort(404, description="Quart error")
```

#### Sanic

```python
from sanic import NotFound

@router.get("/notfound")
async def sanic_notfound():
    raise NotFound()
```

#### Starlette

```python
from starlette.exceptions import HTTPException

@router.get("/notfound")
async def starlette_notfound():
    raise HTTPException(status_code=404, detail="Not Found")
```

#### Tornado

```python
from tornado.web import HTTPError

@router.get("/notfound")
async def tornado_notfound():
    raise HTTPError(status_code=404, reason="Not Found")
```

---
