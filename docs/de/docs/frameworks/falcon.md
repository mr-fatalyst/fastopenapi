# Falcon-Integration

In diesem Leitfaden wird die Verwendung von FastOpenAPI mit **Falcon** beschrieben, einem leistungsstarken Webframework.

FastOpenAPI unterstützt Falcon über den `FalconRouter`, insbesondere bei Verwendung der ASGI-Schnittstelle für asynchrone Anwendungen.

## Installation

FastOpenAPI installieren:

```bash
pip install fastopenapi
```
oder:

```bash
pip install fastopenapi[falcon]
```

## Hello World

```python
import falcon.asgi
import uvicorn
from pydantic import BaseModel
from fastopenapi.routers import FalconRouter

app = falcon.asgi.App()           # ASGI-Anwendung (async-fähig)
router = FalconRouter(app=app)    # FastOpenAPI-Router einbinden

class HelloResponse(BaseModel):
    message: str

@router.get("/hello", tags=["Hello"], response_model=HelloResponse)
async def hello(name: str):
    """Sag Hallo mit Falcon"""
    return HelloResponse(message=f"Hallo, {name}! Hier ist Falcon!")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

## Beispielprojekt

Ein vollständiges Beispiel findest du im Verzeichnis [`examples/falcon/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/falcon) des Repositories.
