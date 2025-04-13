# AIOHTTP-Integration

Dieses Kapitel zeigt, wie man FastOpenAPI mit **AIOHTTP** verwendet (ein asynchrones HTTP-Framework für Python).

AIOHTTP-Anwendungen basieren auf `aiohttp.web.Application` und werden mit `aiohttp.web.run_app` ausgeführt. FastOpenAPI stellt den `AioHttpRouter` zur Integration bereit.

## Installation

Stelle sicher, dass FastOpenAPI installiert ist:

```bash
pip install fastopenapi
```
oder:

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
    """Sag Hallo mit AIOHTTP"""
    return HelloResponse(message=f"Hallo, {name}! Hier ist aiohttp!")

if __name__ == "__main__":
    web.run_app(app, host="127.0.0.1", port=8000)
```

## Beispielprojekt

Ein vollständiges Beispiel findest du im Verzeichnis [`examples/aiohttp/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/aiohttp) des Repositories.
