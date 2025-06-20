from fastopenapi.routers import DjangoRouter

from .v1 import v1_router

api_router = DjangoRouter()
api_router.include_router(v1_router, prefix="/v1")
