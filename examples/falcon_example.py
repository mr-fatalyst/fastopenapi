import falcon.asgi
import uvicorn
from pydantic import BaseModel

from fastopenapi.routers import FalconAsyncRouter

app = falcon.asgi.App()
router = FalconAsyncRouter(app=app)


class HelloResponse(BaseModel):
    message: str


@router.get("/hello", tags=["Hello"], status_code=200, response_model=HelloResponse)
async def hello(name: str):
    """Say hello from Falcon"""
    return HelloResponse(message=f"Hello, {name}! It's Falcon!")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
