from fastopenapi.routers import FlaskRouter

from .authors import router as authors_router
from .posts import router as posts_router

v1_router = FlaskRouter()
v1_router.include_router(authors_router)
v1_router.include_router(posts_router)
