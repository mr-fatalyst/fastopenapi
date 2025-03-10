from fastopenapi.routers.falcon import FalconRouter

from .v1 import v1_router

api_router = FalconRouter()
api_router.include_router(v1_router, prefix="/v1")
