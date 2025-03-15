from fastopenapi.routers import StarletteRouter

from .v1 import v1_router

api_router = StarletteRouter()
api_router.include_router(v1_router, prefix="/v1")
