# Falcon Integration

This guide covers using FastOpenAPI with **Falcon**, a high-performance web framework.

FastOpenAPI's `FalconRouter` supports Falcon, particularly via Falcon's ASGI interface for asynchronous operation.

## Setup

Install FastOpenAPI:
```bash
pip install fastopenapi
```
or
```bash
pip install fastopenapi[falcon]
```

## Hello World

```python
import falcon.asgi
import uvicorn
from pydantic import BaseModel
from fastopenapi.routers import FalconRouter

app = falcon.asgi.App()           # Falcon ASGI app (for async support)
router = FalconRouter(app=app)    # Attach FastOpenAPI router

class HelloResponse(BaseModel):
    message: str

@router.get("/hello", tags=["Hello"], response_model=HelloResponse)
async def hello(name: str):
    """Say hello from Falcon"""
    return HelloResponse(message=f"Hello, {name}! It's Falcon!")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

```

## Project Example

See example for this framework in the [`examples/falcon/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/falcon) directory of the repository.
