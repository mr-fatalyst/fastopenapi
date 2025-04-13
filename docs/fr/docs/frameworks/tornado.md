# Intégration avec Tornado

Tornado est un framework web Python mature et une bibliothèque réseau asynchrone.

FastOpenAPI prend en charge Tornado via `TornadoRouter`, ce qui permet d’ajouter de la documentation OpenAPI aux applications Tornado.

## Installation

Installez FastOpenAPI :

```bash
pip install fastopenapi
```
ou

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
    """Dire bonjour avec Tornado"""
    return HelloResponse(message=f"Bonjour, {name} ! C’est Tornado !")

async def main():
    app.listen(8000)
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
```

## Exemple de projet

Un exemple complet est disponible dans le dossier [`examples/tornado/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/tornado) du dépôt.
