from fastopenapi.routers import AioHttpRouter

from .v1 import v1_router

api_router = AioHttpRouter()
api_router.include_router(v1_router, prefix="/v1")
