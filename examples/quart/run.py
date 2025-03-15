from app.api.routes import api_router
from quart import Quart

from fastopenapi.routers import QuartRouter

app = Quart(__name__)

router = QuartRouter(
    app=app,
    title="MyQuartApp",
    version="0.0.1",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_version="3.0.0",
)
router.include_router(api_router, prefix="/api")


if __name__ == "__main__":
    app.run(debug=True, port=8000)
