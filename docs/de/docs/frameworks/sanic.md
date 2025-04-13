# Sanic-Integration

Sanic ist ein asynchrones Webframework, das für seine Geschwindigkeit bekannt ist.

FastOpenAPI integriert sich in Sanic über den `SanicRouter`.

## Installation

FastOpenAPI installieren:

```bash
pip install fastopenapi
```
oder

```bash
pip install fastopenapi[sanic]
```

## Hello World

```python
from sanic import Sanic
from pydantic import BaseModel
from fastopenapi.routers import SanicRouter

app = Sanic("MySanicApp")
router = SanicRouter(app=app)

class HelloResponse(BaseModel):
    message: str

@router.get("/hello", tags=["Hello"], response_model=HelloResponse)
async def hello(name: str):
    """Sag Hallo mit Sanic"""
    return HelloResponse(message=f"Hallo, {name}! Hier ist Sanic!")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

## Beispielprojekt

Ein vollständiges Beispiel findest du im Verzeichnis [`examples/sanic/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/sanic) des Repositories.
