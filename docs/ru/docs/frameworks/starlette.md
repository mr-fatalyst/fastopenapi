# Интеграция с Starlette

Starlette — это лёгкий ASGI-фреймворк, на базе которого построен сам FastAPI.

`StarletteRouter` от FastOpenAPI позволяет использовать FastOpenAPI напрямую в приложениях Starlette.

## Установка

Установите FastOpenAPI:
```bash
pip install fastopenapi
```
или
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
    """Say hello from Starlette"""
    return HelloResponse(message=f"Hello, {name}! It's Starlette!")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

## Пример проекта

См. пример для этого фреймворка в директории [`examples/starlette/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/starlette) репозитория.
