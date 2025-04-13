# API-Referenz

In diesem Abschnitt findest du eine detaillierte Referenz zu den Klassen und Modulen von FastOpenAPI, inklusive Schnittstellen, Methoden und konkreter Anwendungsbeispiele.

## Projektstruktur

FastOpenAPI verwendet eine modulare Architektur:

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

**Beschreibung:** Abstrakte Basisklasse, die Routing-Logik, OpenAPI-Schema-Generierung und Validierungsverhalten kapselt. Wird von den Framework-spezifischen Routern geerbt.

### Wichtige Methoden

- `__init__(...)`
- `get(path, **options)`: Registriert einen GET-Endpunkt.
- `post(path, **options)`: Registriert einen POST-Endpunkt.
- `put(path, **options)`: Registriert einen PUT-Endpunkt.
- `patch(path, **options)`: Registriert einen PATCH-Endpunkt.
- `delete(path, **options)`: Registriert einen DELETE-Endpunkt.
- `include_router(other_router, prefix="")`: Ermöglicht das Einbinden anderer Router unter einem Präfix.
- `generate_openapi_schema()`: Erzeugt das OpenAPI-Schema.

### Attribute

- `app`: Das verbundene Framework-Objekt.
- `docs_url`, `redoc_url`, `openapi_url`: Endpunkte für die Dokumentation.
- `title`, `description`, `version`: Metadaten für die OpenAPI-Dokumentation.

---

## Framework-Router

Jedes unterstützte Framework hat einen eigenen Router, der von `BaseRouter` erbt:

- **AioHttpRouter**
- **FalconRouter**
- **FlaskRouter**
- **QuartRouter**
- **SanicRouter**
- **StarletteRouter**
- **TornadoRouter**

---

## Subrouter verwenden

Du kannst Routen modular strukturieren:

```python
api_v1 = <Framework>Router()

@api_v1.get("/users")
def users():
    return [{"name": "Alice"}, {"name": "Bob"}]

main_router = <Framework>Router(app=app)
main_router.include_router(api_v1, prefix="/v1")
```

---

## Fehlerbehandlung

### Bibliotheksinterne Fehlerklassen

```python
from fastopenapi.error_handler import BadRequestError, ResourceNotFoundError

@router.get("/validate")
def validate_input(param: int):
    if param < 0:
        raise BadRequestError("Parameter muss positiv sein")

@router.get("/items/{item_id}")
def get_item(item_id: int):
    item = db.get(item_id)
    if item is None:
        raise ResourceNotFoundError(f"Item {item_id} nicht gefunden")
```

### Fehlerbehandlung je Framework

FastOpenAPI unterstützt auch Framework-eigene Fehler:

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

