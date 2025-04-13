# AIOHTTP Integration

This guide covers how to use FastOpenAPI with **AIOHTTP** (an asynchronous HTTP framework).

AIOHTTP applications are usually built with an `aiohttp.web.Application` and run using `aiohttp.web.run_app`. FastOpenAPI provides an `AioHttpRouter` to integrate with this.

## Setup

Make sure you have installed FastOpenAPI:
```bash
pip install fastopenapi
```
or
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

## Project Example

See example for this framework in the [`examples/aiohttp/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/aiohttp) directory of the repository.
