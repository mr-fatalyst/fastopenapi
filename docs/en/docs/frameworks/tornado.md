# Tornado Integration

Tornado is a mature Python web framework and asynchronous networking library.

FastOpenAPI supports Tornado via the `TornadoRouter`, allowing you to add OpenAPI documentation to Tornado applications.

## Setup

Install FastOpenAPI:
```bash
pip install fastopenapi
```
or
```bash
pip install fastopenapi[tornado]
```

## Hello World

```python
import asyncio
from pydantic import BaseModel
from tornado.web import Application
from fastopenapi.routers import TornadoRouter

app = Application()
router = TornadoRouter(app=app)

class HelloResponse(BaseModel):
    message: str

@router.get("/hello", tags=["Hello"], response_model=HelloResponse)
def hello(name: str):
    """Say hello from Tornado"""
    return HelloResponse(message=f"Hello, {name}! It's Tornado!")

async def main():
    app.listen(8000)
    await asyncio.Event().wait()  # Keep running

if __name__ == "__main__":
    asyncio.run(main())

```

## Project Example

See example for this framework in the [`examples/tornado/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/tornado) directory of the repository.
