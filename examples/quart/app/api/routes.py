from fastopenapi.routers import QuartRouter

from .v1 import v1_router

api_router = QuartRouter()
api_router.include_router(v1_router, prefix="/v1")
