# Интеграция с Sanic

Sanic — это асинхронный веб-фреймворк, известный своей высокой производительностью.

FastOpenAPI интегрируется с Sanic с помощью `SanicRouter`.

## Установка

Установите FastOpenAPI:
```bash
pip install fastopenapi
```
или
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
    """Say hello from Sanic"""
    return HelloResponse(message=f"Hello, {name}! It's Sanic!")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

## Пример проекта

См. пример для этого фреймворка в директории [`examples/sanic/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/sanic) репозитория.
