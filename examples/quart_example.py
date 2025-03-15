from pydantic import BaseModel
from quart import Quart

from fastopenapi.routers import QuartRouter

app = Quart(__name__)
router = QuartRouter(app=app, docs_url="/docs", openapi_version="3.0.0")


class HelloResponse(BaseModel):
    message: str


@router.get("/hello", tags=["Hello"], status_code=200, response_model=HelloResponse)
async def hello(name: str):
    """Say hello from Quart"""
    return HelloResponse(message=f"Hello, {name}! It's Quart!")


if __name__ == "__main__":
    app.run(port=8000)
