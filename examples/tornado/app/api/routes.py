from fastopenapi.routers import TornadoRouter

from .v1 import v1_router

api_router = TornadoRouter()
api_router.include_router(v1_router, prefix="/v1")
