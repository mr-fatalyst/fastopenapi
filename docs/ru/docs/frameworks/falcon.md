# Интеграция с Falcon

Это руководство описывает использование FastOpenAPI с **Falcon**, высокопроизводительным веб-фреймворком.

Роутер `FalconRouter` от FastOpenAPI поддерживает Falcon, особенно через ASGI-интерфейс для асинхронной работы.

## Установка

Установите FastOpenAPI:
```bash
pip install fastopenapi
```
или
```bash
pip install fastopenapi[falcon]
```

## Hello World

```python
import falcon.asgi
import uvicorn
from pydantic import BaseModel
from fastopenapi.routers import FalconRouter

app = falcon.asgi.App()           # ASGI-приложение Falcon (для поддержки async)
router = FalconRouter(app=app)    # Подключение роутера FastOpenAPI

class HelloResponse(BaseModel):
    message: str

@router.get("/hello", tags=["Hello"], response_model=HelloResponse)
async def hello(name: str):
    """Say hello from Falcon"""
    return HelloResponse(message=f"Hello, {name}! It's Falcon!")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

## Пример проекта

См. пример для этого фреймворка в директории [`examples/falcon/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/falcon) репозитория.
