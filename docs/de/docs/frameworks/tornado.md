# Tornado-Integration

Tornado ist ein etabliertes Webframework und eine asynchrone Netzwerkbibliothek für Python.

FastOpenAPI unterstützt Tornado über den `TornadoRouter`, mit dem du OpenAPI-Dokumentation zu Tornado-Anwendungen hinzufügen kannst.

## Installation

FastOpenAPI installieren:

```bash
pip install fastopenapi
```
oder

```bash
pip install fastopenapi[tornado]
```

## Hello World

```python
import asyncio
from pydantic import BaseModel
from tornado.web import Application
from fastopenapi.routers import TornadoRouter

app = Application()
router = TornadoRouter(app=app)

class HelloResponse(BaseModel):
    message: str

@router.get("/hello", tags=["Hello"], response_model=HelloResponse)
def hello(name: str):
    """Sag Hallo mit Tornado"""
    return HelloResponse(message=f"Hallo, {name}! Hier ist Tornado!")

async def main():
    app.listen(8000)
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
```

## Beispielprojekt

Ein vollständiges Beispiel findest du im Verzeichnis [`examples/tornado/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/tornado) des Repositories.
