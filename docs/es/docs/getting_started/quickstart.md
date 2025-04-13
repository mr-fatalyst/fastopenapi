# Inicio Rápido

Esta guía te mostrará cómo añadir FastOpenAPI a una aplicación sencilla y cómo ver la documentación API generada automáticamente.

### Paso 0. Instalar la biblioteca  
Sigue las instrucciones de la sección [Instalación](installation.md)

### Paso 1. Crear una aplicación

- Crea un archivo llamado `main.py`
- Copia el código desde uno de los ejemplos
- Algunos ejemplos requieren uvicorn (`pip install uvicorn`)

#### Ejemplos

##### AioHTTP
<details>
<summary>Click to expand the AioHttp Example</summary>
```python
from aiohttp import web
from pydantic import BaseModel

from fastopenapi.routers import AioHttpRouter

app = web.Application()
router = AioHttpRouter(app=app)


class HelloResponse(BaseModel):
    message: str


@router.get("/hello", tags=["Hello"], status_code=200, response_model=HelloResponse)
async def hello(name: str):
    """Say hello from aiohttp"""
    return HelloResponse(message=f"Hello, {name}! It's aiohttp!")


if __name__ == "__main__":
    web.run_app(app, host="127.0.0.1", port=8000)
```
</details>

##### Falcon
<details>
<summary>Click to expand the Falcon Example</summary>

```python
import falcon.asgi
import uvicorn
from pydantic import BaseModel

from fastopenapi.routers import FalconRouter

app = falcon.asgi.App()
router = FalconRouter(app=app)


class HelloResponse(BaseModel):
    message: str


@router.get("/hello", tags=["Hello"], status_code=200, response_model=HelloResponse)
async def hello(name: str):
    """Say hello from Falcon"""
    return HelloResponse(message=f"Hello, {name}! It's Falcon!")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

```
</details>

##### Flask
<details>
<summary>Click to expand the Flask Example</summary>

```python
from flask import Flask
from pydantic import BaseModel

from fastopenapi.routers import FlaskRouter

app = Flask(__name__)
router = FlaskRouter(app=app)


class HelloResponse(BaseModel):
    message: str


@router.get("/hello", tags=["Hello"], status_code=200, response_model=HelloResponse)
def hello(name: str):
    """Say hello from Flask"""
    return HelloResponse(message=f"Hello, {name}! It's Flask!")


if __name__ == "__main__":
    app.run(port=8000)

```
</details>

##### Quart
<details>
<summary>Click to expand the Quart Example</summary>

```python
from pydantic import BaseModel
from quart import Quart

from fastopenapi.routers import QuartRouter

app = Quart(__name__)
router = QuartRouter(app=app)


class HelloResponse(BaseModel):
    message: str


@router.get("/hello", tags=["Hello"], status_code=200, response_model=HelloResponse)
async def hello(name: str):
    """Say hello from Quart"""
    return HelloResponse(message=f"Hello, {name}! It's Quart!")


if __name__ == "__main__":
    app.run(port=8000)

```
</details>

##### Sanic
<details>
<summary>Click to expand the Sanic Example</summary>

```python
from pydantic import BaseModel
from sanic import Sanic

from fastopenapi.routers import SanicRouter

app = Sanic("MySanicApp")
router = SanicRouter(app=app)


class HelloResponse(BaseModel):
    message: str


@router.get("/hello", tags=["Hello"], status_code=200, response_model=HelloResponse)
async def hello(name: str):
    """Say hello from Sanic"""
    return HelloResponse(message=f"Hello, {name}! It's Sanic!")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

```
</details>

##### Starlette
<details>
<summary>Click to expand the Starlette Example</summary>
  
```python
import uvicorn
from pydantic import BaseModel
from starlette.applications import Starlette

from fastopenapi.routers import StarletteRouter

app = Starlette()
router = StarletteRouter(app=app)


class HelloResponse(BaseModel):
    message: str


@router.get("/hello", tags=["Hello"], status_code=200, response_model=HelloResponse)
async def hello(name: str):
    """Say hello from Starlette"""
    return HelloResponse(message=f"Hello, {name}! It's Starlette!")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

```
</details>

##### Tornado
<details>
<summary>Click to expand the Tornado Example</summary>

```python
import asyncio
from pydantic import BaseModel
from tornado.web import Application
from fastopenapi.routers.tornado import TornadoRouter

app = Application()
router = TornadoRouter(app=app)

class HelloResponse(BaseModel):
    message: str

@router.get("/hello", tags=["Hello"], status_code=200, response_model=HelloResponse)
def hello(name: str):
    """Say hello from Tornado"""
    return HelloResponse(message=f"Hello, {name}! It's Tornado!")

async def main():
    app.listen(8000)
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())

```
</details>

### Paso 2. Ejecutar el servidor

```bash
python main.py
```

Una vez que esté corriendo, abre tu navegador:

#### Swagger UI
```
http://127.0.0.1:8000/docs
```

![Swagger UI](../img/HelloSwagger.jpg)

#### ReDoc
```
http://127.0.0.1:8000/redoc
```

![ReDoc](../img/HelloRedoc.jpg)

---

### Rutas generadas automáticamente

- Swagger UI: http://localhost:8000/docs  
- ReDoc: http://localhost:8000/redoc  
- OpenAPI JSON: http://localhost:8000/openapi.json
