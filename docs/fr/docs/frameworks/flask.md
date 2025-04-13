# Intégration avec Flask

Ce guide explique comment intégrer FastOpenAPI avec **Flask**, l’un des frameworks web Python les plus populaires.

La classe `FlaskRouter` permet de lier FastOpenAPI au système de routage de Flask.

## Installation

Installez FastOpenAPI :

```bash
pip install fastopenapi
```
ou :

```bash
pip install fastopenapi[flask]
```

## Hello World

```python
from flask import Flask
from pydantic import BaseModel
from fastopenapi.routers import FlaskRouter

app = Flask(__name__)
router = FlaskRouter(app=app)

class HelloResponse(BaseModel):
    message: str

@router.get("/hello", tags=["Hello"], response_model=HelloResponse)
def hello(name: str):
    """Dire bonjour avec Flask"""
    return HelloResponse(message=f"Bonjour, {name} ! C’est Flask !")

if __name__ == "__main__":
    app.run(port=8000)
```

## Exemple de projet

Un exemple complet est disponible dans le dossier [`examples/flask/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/flask) du dépôt.
