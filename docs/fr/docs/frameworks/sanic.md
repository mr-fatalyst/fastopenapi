# Intégration avec Sanic

Sanic est un framework web asynchrone connu pour sa rapidité.

FastOpenAPI s’intègre à Sanic via le `SanicRouter`.

## Installation

Installez FastOpenAPI :

```bash
pip install fastopenapi
```
ou :

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
    """Dire bonjour avec Sanic"""
    return HelloResponse(message=f"Bonjour, {name} ! C’est Sanic !")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

## Exemple de projet

Consultez le dossier [`examples/sanic/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/sanic) pour un exemple complet.
