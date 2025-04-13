# Intégration AIOHTTP

Ce guide explique comment utiliser FastOpenAPI avec **AIOHTTP**, un framework HTTP asynchrone pour Python.

Les applications AIOHTTP sont construites avec `aiohttp.web.Application` et exécutées avec `aiohttp.web.run_app`. FastOpenAPI fournit le routeur `AioHttpRouter` pour s’y intégrer.

## Installation

Assurez-vous que FastOpenAPI est installé :

```bash
pip install fastopenapi
```
ou :

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
    """Dire bonjour avec AIOHTTP"""
    return HelloResponse(message=f"Bonjour, {name} ! C'est aiohttp !")

if __name__ == "__main__":
    web.run_app(app, host="127.0.0.1", port=8000)
```

## Exemple de projet

Un exemple complet est disponible dans le répertoire [`examples/aiohttp/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/aiohttp) du dépôt.
