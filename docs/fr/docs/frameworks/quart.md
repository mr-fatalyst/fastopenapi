# Intégration avec Quart

Quart est un framework web asynchrone avec une API très proche de Flask (c’est un remplacement direct avec support async).

FastOpenAPI fournit `QuartRouter` pour une intégration fluide avec Quart.

## Installation

Installez FastOpenAPI :

```bash
pip install fastopenapi
```
ou :

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
    """Dire bonjour avec Quart"""
    return HelloResponse(message=f"Bonjour, {name} ! C’est Quart !")

if __name__ == "__main__":
    app.run(port=8000)
```

## Exemple de projet

Consultez le dossier [`examples/quart/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/quart) pour un exemple complet.
