import asyncio

from pydantic import BaseModel
from tornado.web import Application

from fastopenapi.routers.tornado import TornadoRouter

app = Application()

router = TornadoRouter(
    app=app, docs_url="/docs", openapi_url="/openapi.json", openapi_version="3.0.0"
)


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
