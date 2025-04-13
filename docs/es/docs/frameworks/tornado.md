# Integración con Tornado

Tornado es un framework web maduro y una biblioteca de red asíncrona para Python.

FastOpenAPI es compatible con Tornado mediante `TornadoRouter`, lo que permite añadir documentación OpenAPI a las aplicaciones Tornado.

## Instalación

Instala FastOpenAPI:

```bash
pip install fastopenapi
```
o

```bash
pip install fastopenapi[tornado]
```

## Hello World

```python
import asyncio
from pydantic import BaseModel
from tornado.web import Application
from fastopenapi.routers import TornadoRouter

app = Application()
router = TornadoRouter(app=app)

class HelloResponse(BaseModel):
    message: str

@router.get("/hello", tags=["Hello"], response_model=HelloResponse)
def hello(name: str):
    """Saludo desde Tornado"""
    return HelloResponse(message=f"Hola, {name}! Esto es Tornado!")

async def main():
    app.listen(8000)
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
```

## Proyecto de ejemplo

Consulta el directorio [`examples/tornado/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/tornado) del repositorio.
