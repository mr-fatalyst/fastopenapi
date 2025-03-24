from aiohttp import web
from app.api.routes import api_router

from fastopenapi.routers import AioHttpRouter

app = web.Application()

router = AioHttpRouter(
    app=app,
    title="MyAioHttpApp",
    version="0.0.1",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_version="3.0.0",
)
router.include_router(api_router, prefix="/api")


if __name__ == "__main__":
    web.run_app(app, host="127.0.0.1", port=8000)
