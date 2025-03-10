from fastopenapi.routers.sanic import SanicRouter

from .v1 import v1_router

api_router = SanicRouter()
api_router.include_router(v1_router, prefix="/v1")
