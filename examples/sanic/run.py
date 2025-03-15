import uvicorn
from app.api.routes import api_router
from sanic import Sanic

from fastopenapi.routers import SanicRouter

app = Sanic("MySanicApp")

router = SanicRouter(
    app=app,
    title="MySanicApp",
    version="0.0.1",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_version="3.0.0",
)
router.include_router(api_router, prefix="/api")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
