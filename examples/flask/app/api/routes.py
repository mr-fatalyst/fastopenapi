from fastopenapi.routers.flask import FlaskRouter

from .v1 import v1_router

api_router = FlaskRouter()
api_router.include_router(v1_router, prefix="/v1")
