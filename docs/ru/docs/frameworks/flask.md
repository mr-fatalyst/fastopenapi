# Интеграция с Flask

Это руководство демонстрирует, как интегрировать FastOpenAPI с **Flask** — одним из самых популярных веб-фреймворков на Python.

Класс `FlaskRouter` связывает FastOpenAPI с системой маршрутизации Flask.

## Установка

Установите FastOpenAPI:
```bash
pip install fastopenapi
```
или
```bash
pip install fastopenapi[flask]
```

## Hello World

```python
from flask import Flask
from pydantic import BaseModel
from fastopenapi.routers import FlaskRouter

app = Flask(__name__)
router = FlaskRouter(app=app)  # Подключение FastOpenAPI к Flask

class HelloResponse(BaseModel):
    message: str

@router.get("/hello", tags=["Hello"], response_model=HelloResponse)
def hello(name: str):
    """Say hello from Flask"""
    return HelloResponse(message=f"Hello, {name}! It's Flask!")

if __name__ == "__main__":
    app.run(port=8000)
```

## Пример проекта

См. пример использования этого фреймворка в директории [`examples/flask/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/flask) репозитория.
