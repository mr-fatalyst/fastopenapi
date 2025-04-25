from app.api.routes import api_router
from django.urls import path

from fastopenapi.routers import DjangoRouter

router = DjangoRouter(
    app=True,
    title="MyDjangoApp",
    version="0.0.1",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_version="3.0.0",
)
router.include_router(api_router, prefix="/api")

urlpatterns = [
    path("", router.urls),
]
