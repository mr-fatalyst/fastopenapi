# Quart-Integration

Quart ist ein asynchrones Webframework mit einer API, die Flask sehr ähnlich ist (quasi ein Ersatz mit async-Unterstützung).

FastOpenAPI bietet mit `QuartRouter` eine Integration speziell für Quart.

## Installation

FastOpenAPI installieren:

```bash
pip install fastopenapi
```
oder

```bash
pip install fastopenapi[quart]
```

## Hello World

```python
from quart import Quart
from pydantic import BaseModel
from fastopenapi.routers import QuartRouter

app = Quart(__name__)
router = QuartRouter(app=app)

class HelloResponse(BaseModel):
    message: str

@router.get("/hello", tags=["Hello"], response_model=HelloResponse)
async def hello(name: str):
    """Sag Hallo mit Quart"""
    return HelloResponse(message=f"Hallo, {name}! Hier ist Quart!")

if __name__ == "__main__":
    app.run(port=8000)
```

## Beispielprojekt

Ein vollständiges Beispiel findest du im Verzeichnis [`examples/quart/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/quart) des Repositories.
