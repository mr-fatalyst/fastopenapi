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
