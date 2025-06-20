# Справочник API

В этом разделе представлен подробный справочник по классам и модулям FastOpenAPI, включая интерфейсы, методы и примеры использования.

## Структура файлов

FastOpenAPI использует модульную архитектуру:

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
    ├── tornado.py
    └── django.py
```

---

## BaseRouter

**Описание:** Абстрактный базовый класс, реализующий общую маршрутизацию и генерацию схемы OpenAPI. Обычно используется как базовый класс для роутеров под конкретные фреймворки.

### Основные методы

- `__init__(...)`
- `get(path, **options)`: Определяет GET-маршрут.
- `post(path, **options)`: Определяет POST-маршрут.
- `put(path, **options)`: Определяет PUT-маршрут.
- `patch(path, **options)`: Определяет PATCH-маршрут.
- `delete(path, **options)`: Определяет DELETE-маршрут.
- `include_router(other_router, prefix="")`: Подключает маршруты другого роутера с префиксом.
- `generate_openapi_schema()`: Генерация OpenAPI-схемы.

### Атрибуты

- `app`: Инстанс приложения (фреймворк-специфичный).
- `docs_url`, `redoc_url`, `openapi_url`: Пути к документации.
- `title`, `description`, `version`: Метаданные OpenAPI.

---

## Роутеры для фреймворков

Каждый роутер наследуется от `BaseRouter` и адаптирован под конкретный фреймворк.

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

### DjangoRouter

Use for Django integration.

```python
from django.urls import path
from fastopenapi.routers import DjangoRouter

router = DjangoRouter(app=True)

@router.get("/status")
async def status():
    return {"status": "ok"}

urlpatterns = [path("", router.urls)]
```

---

## Подроутеры

Вы можете объединять маршруты через `include_router`:

```python
api_v1 = <Framework>Router()

@api_v1.get("/users")
def users():
    return [{"name": "Alice"}, {"name": "Bob"}]

main_router = <Framework>Router(app=app)
main_router.include_router(api_v1, prefix="/v1")
```

---

## Обработка исключений

### Встроенные исключения

```python
from fastopenapi.error_handler import BadRequestError, ResourceNotFoundError

@router.get("/validate")
def validate_input(param: int):
    if param < 0:
        raise BadRequestError("Parameter must be positive")

@router.get("/items/{item_id}")
def get_item(item_id: int):
    item = db.get(item_id)
    if item is None:
        raise ResourceNotFoundError(f"Item {item_id} not found")
```

### Исключения фреймворков

FastOpenAPI также позволяет использовать исключения родного фреймворка:

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

