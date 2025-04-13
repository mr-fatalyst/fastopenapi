# Интеграция с AIOHTTP

Это руководство описывает, как использовать FastOpenAPI с **AIOHTTP** (асинхронным HTTP-фреймворком).

Приложения на AIOHTTP обычно создаются с использованием `aiohttp.web.Application` и запускаются через `aiohttp.web.run_app`. FastOpenAPI предоставляет `AioHttpRouter` для интеграции с этим фреймворком.

## Установка

Убедитесь, что установлен FastOpenAPI:
```bash
pip install fastopenapi
```
или
```bash
pip install fastopenapi[aiohttp]
```

## Hello World

```python
from aiohttp import web
from pydantic import BaseModel
from fastopenapi.routers import AioHttpRouter

app = web.Application()
router = AioHttpRouter(app=app)

class HelloResponse(BaseModel):
    message: str

@router.get("/hello", tags=["Hello"], response_model=HelloResponse)
async def hello(name: str):
    """Say hello from AIOHTTP"""
    return HelloResponse(message=f"Hello, {name}! It's aiohttp!")

if __name__ == "__main__":
    web.run_app(app, host="127.0.0.1", port=8000)
```

## Пример проекта

См. пример для этого фреймворка в директории [`examples/aiohttp/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/aiohttp) репозитория.
