# Intégration avec Starlette

Starlette est un framework ASGI léger sur lequel repose FastAPI lui-même.

Le `StarletteRouter` de FastOpenAPI permet une intégration directe avec les applications Starlette.

## Installation

Installez FastOpenAPI :

```bash
pip install fastopenapi
```
ou :

```bash
pip install fastopenapi[starlette]
```

## Hello World

```python
import uvicorn
from pydantic import BaseModel
from starlette.applications import Starlette
from fastopenapi.routers import StarletteRouter

app = Starlette()
router = StarletteRouter(app=app)

class HelloResponse(BaseModel):
    message: str

@router.get("/hello", tags=["Hello"], response_model=HelloResponse)
async def hello(name: str):
    """Dire bonjour avec Starlette"""
    return HelloResponse(message=f"Bonjour, {name} ! C’est Starlette !")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

## Exemple de projet

Consultez le dossier [`examples/starlette/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/starlette) pour un exemple complet.
