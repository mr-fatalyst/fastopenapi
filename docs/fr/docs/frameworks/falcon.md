# Intégration avec Falcon

Ce guide présente l’utilisation de FastOpenAPI avec **Falcon**, un framework web haute performance.

Le `FalconRouter` de FastOpenAPI prend en charge Falcon, notamment via son interface ASGI pour les opérations asynchrones.

## Installation

Installez FastOpenAPI :

```bash
pip install fastopenapi
```
ou :

```bash
pip install fastopenapi[falcon]
```

## Hello World

```python
import falcon.asgi
import uvicorn
from pydantic import BaseModel
from fastopenapi.routers import FalconRouter

app = falcon.asgi.App()
router = FalconRouter(app=app)

class HelloResponse(BaseModel):
    message: str

@router.get("/hello", tags=["Hello"], response_model=HelloResponse)
async def hello(name: str):
    """Dire bonjour avec Falcon"""
    return HelloResponse(message=f"Bonjour, {name} ! C’est Falcon !")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

## Exemple de projet

Un exemple complet est disponible dans le dossier [`examples/falcon/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/falcon) du dépôt.
