# Quart Integration

Quart is an async web framework with a Flask-like API (it’s a drop-in replacement for Flask but with async support).

FastOpenAPI provides `QuartRouter` for integrating with Quart.

## Setup

Install FastOpenAPI:
```bash
pip install fastopenapi
```
or
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

## Project Example

See example for this framework in the [`examples/quart/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/quart) directory of the repository.
