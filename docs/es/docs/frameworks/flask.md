# Integración con Flask

Esta guía muestra cómo integrar FastOpenAPI con **Flask**, uno de los frameworks web más populares de Python.

La clase `FlaskRouter` conecta FastOpenAPI con el sistema de rutas de Flask.

## Instalación

Instala FastOpenAPI:

```bash
pip install fastopenapi
```
o:

```bash
pip install fastopenapi[flask]
```

## Hello World

```python
from flask import Flask
from pydantic import BaseModel
from fastopenapi.routers import FlaskRouter

app = Flask(__name__)
router = FlaskRouter(app=app)  # Enlazar con FastOpenAPI

class HelloResponse(BaseModel):
    message: str

@router.get("/hello", tags=["Hello"], response_model=HelloResponse)
def hello(name: str):
    """Saludo desde Flask"""
    return HelloResponse(message=f"Hola, {name}! Esto es Flask!")

if __name__ == "__main__":
    app.run(port=8000)
```

## Proyecto de ejemplo

Consulta el directorio [`examples/flask/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/flask) para ver un ejemplo funcional.
