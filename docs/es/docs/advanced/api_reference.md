# Referencia API

Esta sección proporciona una referencia detallada de las clases, funciones y módulos que componen FastOpenAPI. Es útil para comprender en profundidad las interfaces disponibles y cómo usarlas.

## Estructura del proyecto

FastOpenAPI usa una arquitectura modular:

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

**Descripción:** Clase base que define la interfaz común para todos los routers. No se usa directamente, pero todas las clases de router específicas de frameworks heredan de ella.

**Métodos clave:**

- `BaseRouter.__init__(app)`: Inicializa el router con una aplicación del framework.
- `get(path, **options)`: Registra una ruta GET.
- `post(path, **options)`: Registra una ruta POST.
- `put(path, **options)`: Registra una ruta PUT.
- `patch(path, **options)`: Registra una ruta PATCH.
- `delete(path, **options)`: Registra una ruta DELETE.
- `include_router(other_router, prefix="")`: Permite incluir subrouters.
- `generate_openapi_schema()`: Devuelve el esquema OpenAPI generado.
- `get_openapi_schema()`: Igual que el anterior, pero con caché.

**Atributos:**

- `app`: Referencia a la app del framework.
- `routes`: Lista de rutas registradas.
- `docs_url`, `redoc_url`, `openapi_url`: URLs de documentación generada.
- `title`, `version`, `description`: Metadatos del esquema OpenAPI.

---

## Routers por framework

FastOpenAPI ofrece una clase de router por framework.
Cada uno extiende `BaseRouter` y adapta las rutas a las interfaces específicas del framework.

### AioHttpRouter

```python
from aiohttp import web
from fastopenapi.routers import AioHttpRouter

app = web.Application()
router = AioHttpRouter(app=app)

@router.get("/status")
async def status():
    return {"status": "ok"}
```

---

### FalconRouter

```python
import falcon.asgi
from fastopenapi.routers import FalconRouter

app = falcon.asgi.App()
router = FalconRouter(app=app)

@router.get("/status")
async def status():
    return {"status": "ok"}
```

---

### FlaskRouter

```python
from flask import Flask
from fastopenapi.routers import FlaskRouter

app = Flask(__name__)
router = FlaskRouter(app=app)

@router.get("/hello")
def hello(name: str):
    return {"message": f"Hello {name}"}
```

---

### QuartRouter

```python
from quart import Quart
from fastopenapi.routers import QuartRouter

app = Quart(__name__)
router = QuartRouter(app=app)

@router.get("/ping")
async def ping():
    return {"pong": True}
```

---

### SanicRouter

```python
from sanic import Sanic
from fastopenapi.routers import SanicRouter

app = Sanic("MySanicApp")
router = SanicRouter(app=app)

@router.get("/info")
async def info():
    return {"framework": "Sanic", "status": "running"}
```

---

### StarletteRouter

Use for Starlette integration.

```python
from starlette.applications import Starlette
from fastopenapi.routers import StarletteRouter

app = Starlette()
router = StarletteRouter(app=app)

@router.get("/check")
async def check():
    return {"status": "healthy"}
```

---

### TornadoRouter

Use for Tornado integration.

```python
from tornado.web import Application
from fastopenapi.routers import TornadoRouter

app = Application()
router = TornadoRouter(app=app)

@router.get("/status")
def status():
    return {"running": True}
```

---

## Subrouters

Puedes dividir tus rutas en módulos reutilizables:

```python
user_router = StarletteRouter()

@user_router.get("/users")
def list_users():
    return [{"id": 1}, {"id": 2}]

main_router = StarletteRouter(app=app)
main_router.include_router(user_router, prefix="/v1")
```

---

## Manejo de errores

FastOpenAPI permite definir respuestas de error de forma estandarizada. Las excepciones personalizadas como `BadRequestError` o `ResourceNotFoundError` se traducen automáticamente a respuestas JSON estructuradas.

```python
from fastopenapi.error_handler import ResourceNotFoundError

@router.get("/items/{item_id}")
def get_item(item_id: int):
    item = get_from_db(item_id)
    if item is None:
        raise ResourceNotFoundError(f"Ítem {item_id} no encontrado")
    return item
```

### Compatibilidad con excepciones del framework

FastOpenAPI también es compatible con errores del framework:

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

## Extensión

Para extender FastOpenAPI, hereda de `BaseRouter` y adapta:

- el registro de rutas,
- la inicialización de documentación (`/docs`, `/openapi.json`),
- la lógica de ejecución del endpoint.

Consulta el código fuente y usa los routers existentes como referencia.

