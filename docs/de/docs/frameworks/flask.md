# Flask-Integration

Dieser Leitfaden zeigt die Integration von FastOpenAPI mit **Flask**, einem der beliebtesten Python-Webframeworks.

Die Klasse `FlaskRouter` verbindet FastOpenAPI mit dem Routing-System von Flask.

## Installation

FastOpenAPI installieren:

```bash
pip install fastopenapi
```
oder

```bash
pip install fastopenapi[flask]
```

## Hello World

```python
from flask import Flask
from pydantic import BaseModel
from fastopenapi.routers import FlaskRouter

app = Flask(__name__)
router = FlaskRouter(app=app)  # FastOpenAPI-Router einbinden

class HelloResponse(BaseModel):
    message: str

@router.get("/hello", tags=["Hello"], response_model=HelloResponse)
def hello(name: str):
    """Sag Hallo mit Flask"""
    return HelloResponse(message=f"Hallo, {name}! Hier ist Flask!")

if __name__ == "__main__":
    app.run(port=8000)
```

## Beispielprojekt

Ein vollständiges Beispiel findest du im Verzeichnis [`examples/flask/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/flask) des Repositories.
