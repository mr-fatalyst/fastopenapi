import uvicorn
from pydantic import BaseModel
from starlette.applications import Starlette

from fastopenapi.routers.starlette import StarletteRouter

app = Starlette()
router = StarletteRouter(app=app, docs_url="/docs/", openapi_version="3.0.0")


class HelloResponse(BaseModel):
    message: str


@router.get("/hello", tags=["Hello"], status_code=200, response_model=HelloResponse)
async def hello(name: str):
    """Say hello from Starlette"""
    return HelloResponse(message=f"Hello, {name}! It's Starlette!")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
