from app.api.routes import api_router
from flask import Flask

from fastopenapi.routers import FlaskRouter

app = Flask(__name__)

router = FlaskRouter(
    app=app,
    title="MyFlaskApp",
    version="0.0.1",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_version="3.0.0",
)
router.include_router(api_router, prefix="/api")


if __name__ == "__main__":
    app.run(debug=True, port=8000)
