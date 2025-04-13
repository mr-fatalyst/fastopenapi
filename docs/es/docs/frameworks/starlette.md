# Integración con Starlette

Starlette es un framework ASGI liviano sobre el que está construido FastAPI.

`StarletteRouter` de FastOpenAPI permite utilizar FastOpenAPI directamente en aplicaciones Starlette.

## Instalación

Instala FastOpenAPI:

```bash
pip install fastopenapi
```
o:

```bash
pip install fastopenapi[starlette]
```

## Hello World

```python
import uvicorn
from pydantic import BaseModel
from starlette.applications import Starlette
from fastopenapi.routers import StarletteRouter

app = Starlette()
router = StarletteRouter(app=app)

class HelloResponse(BaseModel):
    message: str

@router.get("/hello", tags=["Hello"], response_model=HelloResponse)
async def hello(name: str):
    """Saludo desde Starlette"""
    return HelloResponse(message=f"Hola, {name}! Esto es Starlette!")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

## Proyecto de ejemplo

Consulta el directorio [`examples/starlette/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/starlette) para ver un ejemplo funcional.
