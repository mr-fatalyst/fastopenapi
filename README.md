<p align="center">
  <img src="https://raw.githubusercontent.com/mr-fatalyst/fastopenapi/master/logo.png" alt="Logo">
</p>

<p align="center">
  <b>FastOpenAPI</b> is a library for generating and integrating OpenAPI schemas using Pydantic and various frameworks.
</p>

<p align="center">
  This project was inspired by <a href="https://fastapi.tiangolo.com/">FastAPI</a> and aims to provide a similar developer-friendly experience.
</p>

<p align="center">
  <img src="https://img.shields.io/github/license/mr-fatalyst/fastopenapi">
  <img src="https://github.com/mr-fatalyst/fastopenapi/actions/workflows/master.yml/badge.svg">
  <img src="https://codecov.io/gh/mr-fatalyst/fastopenapi/branch/master/graph/badge.svg?token=USHR1I0CJB">
  <img src="https://img.shields.io/pypi/v/fastopenapi">
  <img src="https://img.shields.io/pypi/pyversions/fastopenapi">
  <img src="https://static.pepy.tech/badge/fastopenapi" alt="PyPI Downloads">
</p>

---


## 📦 Installation
#### Install only FastOpenAPI:
```bash
pip install fastopenapi
```

#### Install FastOpenAPI with a specific framework:
```bash
pip install fastopenapi[aiohttp]
```
```bash
pip install fastopenapi[falcon]
```
```bash
pip install fastopenapi[flask]
```
```bash
pip install fastopenapi[quart]
```
```bash
pip install fastopenapi[sanic]
```
```bash
pip install fastopenapi[starlette]
```
```bash
pip install fastopenapi[tornado]
```

---

## 🛠️ Quick Start

### Step 1. Create an application

- Create the `main.py` file
- Copy the code from an example
- For some examples uvicorn is required (`pip install uvicorn`)

#### Examples:

- ![AIOHTTP](https://img.shields.io/badge/AioHttp-0078D7?style=flat&logo=python&logoColor=white)
  <details>
    <summary>Click to expand the Falcon Example</summary>
    
    ```python
    from aiohttp import web
    from pydantic import BaseModel
    
    from fastopenapi.routers import AioHttpRouter
    
    app = web.Application()
    router = AioHttpRouter(app=app)
    
    
    class HelloResponse(BaseModel):
        message: str
    
    
    @router.get("/hello", tags=["Hello"], status_code=200, response_model=HelloResponse)
    async def hello(name: str):
        """Say hello from aiohttp"""
        return HelloResponse(message=f"Hello, {name}! It's aiohttp!")
    
    
    if __name__ == "__main__":
        web.run_app(app, host="127.0.0.1", port=8000)
    ```
  </details>

- ![Falcon](https://img.shields.io/badge/Falcon-45b8d8?style=flat&logo=falcon&logoColor=white)
  <details>
    <summary>Click to expand the Falcon Example</summary>
    
    ```python
    import falcon.asgi
    import uvicorn
    from pydantic import BaseModel
    
    from fastopenapi.routers import FalconRouter
    
    app = falcon.asgi.App()
    router = FalconRouter(app=app)
    
    
    class HelloResponse(BaseModel):
        message: str
    
    
    @router.get("/hello", tags=["Hello"], status_code=200, response_model=HelloResponse)
    async def hello(name: str):
        """Say hello from Falcon"""
        return HelloResponse(message=f"Hello, {name}! It's Falcon!")
    
    
    if __name__ == "__main__":
        uvicorn.run(app, host="127.0.0.1", port=8000)
    ```
  </details>

- ![Flask](https://img.shields.io/badge/-Flask-EEEEEE?style=flat&logo=flask&logoColor=black)
  <details>
    <summary>Click to expand the Flask Example</summary>
    
    ```python
    from flask import Flask
    from pydantic import BaseModel
    
    from fastopenapi.routers import FlaskRouter
    
    app = Flask(__name__)
    router = FlaskRouter(app=app)
    
    
    class HelloResponse(BaseModel):
        message: str
    
    
    @router.get("/hello", tags=["Hello"], status_code=200, response_model=HelloResponse)
    def hello(name: str):
        """Say hello from Flask"""
        return HelloResponse(message=f"Hello, {name}! It's Flask!")
    
    
    if __name__ == "__main__":
        app.run(port=8000)
    ```
  </details>

- ![Quart](https://img.shields.io/badge/-Quart-4997D0?style=flat&logo=python&logoColor=white)
  <details>
    <summary>Click to expand the Quart Example</summary>
    
    ```python
    from pydantic import BaseModel
    from quart import Quart
    
    from fastopenapi.routers import QuartRouter
    
    app = Quart(__name__)
    router = QuartRouter(app=app)
    
    
    class HelloResponse(BaseModel):
        message: str
    
    
    @router.get("/hello", tags=["Hello"], status_code=200, response_model=HelloResponse)
    async def hello(name: str):
        """Say hello from Quart"""
        return HelloResponse(message=f"Hello, {name}! It's Quart!")
    
    
    if __name__ == "__main__":
        app.run(port=8000)
    ```
  </details>

- ![Sanic](https://img.shields.io/badge/-Sanic-00bfff?style=flat&logo=sanic&logoColor=white)
  <details>
    <summary>Click to expand the Sanic Example</summary>
    
    ```python
    from pydantic import BaseModel
    from sanic import Sanic
    
    from fastopenapi.routers import SanicRouter
    
    app = Sanic("MySanicApp")
    router = SanicRouter(app=app)
    
    
    class HelloResponse(BaseModel):
        message: str
    
    
    @router.get("/hello", tags=["Hello"], status_code=200, response_model=HelloResponse)
    async def hello(name: str):
        """Say hello from Sanic"""
        return HelloResponse(message=f"Hello, {name}! It's Sanic!")
    
    
    if __name__ == "__main__":
        app.run(host="0.0.0.0", port=8000)
    ```
  </details>

- ![Starlette](https://img.shields.io/badge/-Starlette-4B0082?style=flat&logo=python&logoColor=white)
  <details>
    <summary>Click to expand the Starlette Example</summary>
    
    ```python
    import uvicorn
    from pydantic import BaseModel
    from starlette.applications import Starlette
    
    from fastopenapi.routers import StarletteRouter
    
    app = Starlette()
    router = StarletteRouter(app=app)
    
    
    class HelloResponse(BaseModel):
        message: str
    
    
    @router.get("/hello", tags=["Hello"], status_code=200, response_model=HelloResponse)
    async def hello(name: str):
        """Say hello from Starlette"""
        return HelloResponse(message=f"Hello, {name}! It's Starlette!")
    
    if __name__ == "__main__":
        uvicorn.run(app, host="127.0.0.1", port=8000)
    ```
  </details>

- ![Tornado](https://img.shields.io/badge/-Tornado-2980B9?style=flat&logo=python&logoColor=white)
  <details>
    <summary>Click to expand the Tornado Example</summary>
    
    ```python
    import asyncio
  
    from pydantic import BaseModel
    from tornado.web import Application
  
    from fastopenapi.routers.tornado import TornadoRouter
  
    app = Application()
  
    router = TornadoRouter(app=app)
  
  
    class HelloResponse(BaseModel):
        message: str
  
  
    @router.get("/hello", tags=["Hello"], status_code=200, response_model=HelloResponse)
    def hello(name: str):
        """Say hello from Tornado"""
        return HelloResponse(message=f"Hello, {name}! It's Tornado!")
  
  
    async def main():
        app.listen(8000)
        await asyncio.Event().wait()
  
  
    if __name__ == "__main__":
        asyncio.run(main())
    ```
  </details>

### Step 2. Run the server

Launch the application:

```bash
python main.py
```

Once launched, the documentation will be available at:

Swagger UI:
```
http://127.0.0.1:8000/docs
```
ReDoc UI:
```
http://127.0.0.1:8000/redoc
```

---

## ⚙️ Features
- **Generate OpenAPI schemas** with Pydantic v2.
- **Data validation** using Pydantic models.
- **Supports multiple frameworks:** AIOHTTP, Falcon, Flask, Quart, Sanic, Starlette, Tornado.
- **Proxy routing provides FastAPI-style routing**

---

## 📖 Documentation

Explore the [Docs](https://fastopenapi.fatalyst.dev/) for an overview of FastOpenAPI, its core components, and usage guidelines. The documentation is continuously updated and improved.

---

## 📂 Advanced Examples

Examples of integration and detailed usage for each framework are available in the [`examples`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples) directory.

---

## 📊 Quick & Dirty Benchmarks

Fast but not perfect benchmarks. Check the [`benchmarks`](https://github.com/mr-fatalyst/fastopenapi/tree/master/benchmarks) directory for details.

---

## ✅ Development Recommendations

- Use Pydantic models for strict typing and data validation.
- Follow the project structure similar to provided examples for easy scalability.
- Regularly update dependencies and monitor library updates for new features.

---

## 🛠️ Contributing

If you have suggestions or find a bug, please open an issue or create a pull request on GitHub.

---

## 📄 **License**
This project is licensed under the terms of the MIT license.
