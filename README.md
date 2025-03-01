
# 🚀 FastOpenAPI
![Test](https://github.com/mr-fatalyst/fastopenapi/actions/workflows/test.yml/badge.svg)
![codecov](https://codecov.io/gh/mr-fatalyst/fastopenapi/branch/main/graph/badge.svg?token=USHR1I0CJB)

**FastOpenAPI** is a library for generating and integrating OpenAPI schemas using Pydantic v2 and various frameworks (Falcon, Flask, Sanic, Starlette).

---

## 📦 Installation
```bash
pip install fastopenapi
```

---

## ⚙️ Features
- 📄 **Generate OpenAPI schemas** with Pydantic v2.
- 🛡️ **Data validation** using Pydantic models.
- 🛠️ **Supports multiple frameworks:** Falcon, Flask, Sanic, Starlette.
- ✅ **Compatible with Pydantic v2.**

---

## 🛠️ Quick Start

### ![Falcon](https://img.shields.io/badge/Falcon-45b8d8?style=flat&logo=falcon&logoColor=white)
```python
import falcon.asgi
import uvicorn
from pydantic import BaseModel

from fastopenapi.routers.falcon import FalconRouter

app = falcon.asgi.App()
router = FalconRouter(app=app, docs_url="/docs/", openapi_version="3.0.0")


class HelloResponse(BaseModel):
    message: str


@router.get("/hello", tags=["Hello"], status_code=200, response_model=HelloResponse)
async def hello(name: str):
    """Say hello from Falcon"""
    return HelloResponse(message=f"Hello, {name}! It's Falcon!")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

```

---

### ![Flask](https://img.shields.io/badge/-Flask-000000?style=flat-square&logo=flask&logoColor=white)
```python
from flask import Flask
from pydantic import BaseModel

from fastopenapi.routers.flask import FlaskRouter

app = Flask(__name__)
router = FlaskRouter(app=app, docs_url="/docs/", openapi_version="3.0.0")


class HelloResponse(BaseModel):
    message: str


@router.get("/hello", tags=["Hello"], status_code=200, response_model=HelloResponse)
def hello(name: str):
    """Say hello from Flask"""
    return HelloResponse(message=f"Hello, {name}! It's Flask!")


if __name__ == "__main__":
    app.run(debug=True, port=8000)

```

---

### ![Sanic](https://img.shields.io/badge/-Sanic-00bfff?style=flat-square&logo=sanic&logoColor=white)
```python
from pydantic import BaseModel
from sanic import Sanic

from fastopenapi.routers.sanic import SanicRouter

app = Sanic("MySanicApp")
router = SanicRouter(app=app, docs_url="/docs/", openapi_version="3.0.0")


class HelloResponse(BaseModel):
    message: str


@router.get("/hello", tags=["Hello"], status_code=200, response_model=HelloResponse)
async def hello(name: str):
    """Say hello from Sanic"""
    return HelloResponse(message=f"Hello, {name}! It's Sanic!")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)

```

---

### ![Starlette](https://img.shields.io/badge/-Starlette-ff4785?style=flat-square&logo=starlette&logoColor=white)
```python
import uvicorn
from pydantic import BaseModel
from starlette.applications import Starlette

from fastopenapi.routers.starlette import StarletteRouter

app = Starlette()
router = StarletteRouter(app=app, docs_url="/docs/", openapi_version="3.0.0")


class HelloResponse(BaseModel):
    message: str


@router.get("/hello", tags=["Hello"], status_code=200, response_model=HelloResponse)
async def hello(name: str):
    """Say hello from Starlette"""
    return HelloResponse(message=f"Hello, {name}! It's Starlette!")


router.register_routes()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

```

---

## 🛡️ **Type Safety with Pydantic v2**
```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str

@router.post("/api/v1/users/")
def create_user(user: User) -> User:
    return user
```

---

## 🧪 **Running Tests**
```bash
poetry run pytest
```

---

## 📄 **License**
This project is licensed under the terms of the MIT license.
