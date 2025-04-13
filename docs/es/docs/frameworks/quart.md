# Integración con Quart

Quart es un framework web asíncrono con una API muy similar a Flask (es un reemplazo directo compatible con async).

FastOpenAPI proporciona `QuartRouter` para integrarse con aplicaciones construidas en Quart.

## Instalación

Instala FastOpenAPI:

```bash
pip install fastopenapi
```
o:

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
    """Saludo desde Quart"""
    return HelloResponse(message=f"Hola, {name}! Esto es Quart!")

if __name__ == "__main__":
    app.run(port=8000)
```

## Proyecto de ejemplo

Consulta el directorio [`examples/quart/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/quart) para ver un ejemplo completo.
