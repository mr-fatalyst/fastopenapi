# Интеграция с Tornado

Tornado — зрелый веб-фреймворк и асинхронная сетевая библиотека на Python.

FastOpenAPI поддерживает Tornado через `TornadoRouter`, позволяя добавлять документацию OpenAPI к приложениям на Tornado.

## Установка

Установите FastOpenAPI:
```bash
pip install fastopenapi
```
или
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
    """Say hello from Tornado"""
    return HelloResponse(message=f"Hello, {name}! It's Tornado!")

async def main():
    app.listen(8000)
    await asyncio.Event().wait()  # Постоянное ожидание

if __name__ == "__main__":
    asyncio.run(main())
```

## Пример проекта

См. пример для этого фреймворка в директории [`examples/tornado/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/tornado) репозитория.
