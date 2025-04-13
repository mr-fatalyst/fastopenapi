# Starlette Integration

Starlette is a lightweight ASGI framework which FastAPI itself is built upon.

FastOpenAPI's `StarletteRouter` allows you to use FastOpenAPI directly with Starlette applications.

## Setup

Install FastOpenAPI:
```bash
pip install fastopenapi
```
or
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

## Project Example

See example for this framework in the [`examples/starlette/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/starlette) directory of the repository.
