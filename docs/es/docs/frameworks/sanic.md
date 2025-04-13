# Integración con Sanic

Sanic es un framework web asíncrono conocido por su alto rendimiento.

FastOpenAPI se integra con Sanic a través de `SanicRouter`.

## Instalación

Instala FastOpenAPI:

```bash
pip install fastopenapi
```
o:

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
    """Saludo desde Sanic"""
    return HelloResponse(message=f"Hola, {name}! Esto es Sanic!")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

## Proyecto de ejemplo

Puedes consultar el directorio [`examples/sanic/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/sanic) para ver un ejemplo funcional.
