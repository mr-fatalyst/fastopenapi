import uvicorn
from app.api.routes import api_router
from starlette.applications import Starlette

from fastopenapi.routers.starlette import StarletteRouter

app = Starlette()

router = StarletteRouter(
    app=app,
    title="MyStarletteApp",
    version="0.0.1",
    docs_url="/docs/",
    openapi_version="3.0.0",
)
router.include_router(api_router, prefix="/api")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
