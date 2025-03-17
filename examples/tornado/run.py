import asyncio

from app.api.routes import api_router
from tornado.web import Application

from fastopenapi.routers import TornadoRouter

app = Application()

router = TornadoRouter(
    app=app,
    title="MyTornadoApp",
    version="0.0.1",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_version="3.0.0",
)
router.include_router(api_router, prefix="/api")


async def main():
    app.listen(8000)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
