# Integración con AIOHTTP

Esta guía explica cómo utilizar FastOpenAPI con **AIOHTTP** (un framework HTTP asíncrono).

Las aplicaciones con AIOHTTP se construyen típicamente con `aiohttp.web.Application` y se ejecutan usando `aiohttp.web.run_app`. FastOpenAPI proporciona `AioHttpRouter` para integrarse con este framework.

## Instalación

Asegúrate de tener instalado FastOpenAPI:

```bash
pip install fastopenapi
```
o:

```bash
pip install fastopenapi[aiohttp]
```

## Hello World

```python
from aiohttp import web
from pydantic import BaseModel
from fastopenapi.routers import AioHttpRouter

app = web.Application()
router = AioHttpRouter(app=app)

class HelloResponse(BaseModel):
    message: str

@router.get("/hello", tags=["Hello"], response_model=HelloResponse)
async def hello(name: str):
    """Saludo desde AIOHTTP"""
    return HelloResponse(message=f"Hola, {name}! Esto es aiohttp!")

if __name__ == "__main__":
    web.run_app(app, host="127.0.0.1", port=8000)
```

## Proyecto de ejemplo

Puedes encontrar un ejemplo funcional en el directorio [`examples/aiohttp/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/aiohttp) del repositorio.
