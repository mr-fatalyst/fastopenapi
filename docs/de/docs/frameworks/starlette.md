# Starlette-Integration

Starlette ist ein leichtgewichtiges ASGI-Framework, auf dem auch FastAPI selbst basiert.

FastOpenAPI bietet mit `StarletteRouter` eine direkte Integration in Starlette-Anwendungen.

## Installation

FastOpenAPI installieren:

```bash
pip install fastopenapi
```
oder

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
    """Sag Hallo mit Starlette"""
    return HelloResponse(message=f"Hallo, {name}! Hier ist Starlette!")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

## Beispielprojekt

Ein vollständiges Beispiel findest du im Verzeichnis [`examples/starlette/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/starlette) des Repositories.
