# Интеграция с Quart

Quart — это асинхронный веб-фреймворк с API, схожим с Flask (может быть прямой заменой Flask с поддержкой async).

FastOpenAPI предоставляет `QuartRouter` для интеграции с Quart.

## Установка

Установите FastOpenAPI:
```bash
pip install fastopenapi
```
или
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
    """Say hello from Quart"""
    return HelloResponse(message=f"Hello, {name}! It's Quart!")

if __name__ == "__main__":
    app.run(port=8000)
```

## Пример проекта

См. пример использования этого фреймворка в директории [`examples/quart/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/quart) репозитория.
