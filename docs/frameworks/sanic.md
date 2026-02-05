# Sanic Integration

Sanic is an async web framework known for its speed.

FastOpenAPI can integrate with Sanic through the `SanicRouter`.

## Setup

Install FastOpenAPI:
```bash
pip install fastopenapi
```
or
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

## Project Example

See example for this framework in the [`examples/sanic/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/sanic) directory of the repository.
