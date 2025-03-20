import falcon
import uvicorn
from app.api.routes import api_router

from fastopenapi.routers import FalconRouter

app = falcon.asgi.App()

router = FalconRouter(
    app=app,
    title="MyFalconApp",
    version="0.0.1",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_version="3.0.0",
)
router.include_router(api_router, prefix="/api")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
