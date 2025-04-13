# Integración con Falcon

Esta guía explica cómo usar FastOpenAPI con **Falcon**, un framework web de alto rendimiento.

El `FalconRouter` de FastOpenAPI es compatible con Falcon, especialmente usando su interfaz ASGI para soporte asíncrono.

## Instalación

Instala FastOpenAPI:

```bash
pip install fastopenapi
```
o:

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
    """Saludo desde Falcon"""
    return HelloResponse(message=f"Hola, {name}! Esto es Falcon!")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

## Proyecto de ejemplo

Consulta el directorio [`examples/falcon/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/falcon) para un ejemplo funcional.
