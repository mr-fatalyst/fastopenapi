class MissingRouter:
    def __init__(self, *args, **kwargs):
        raise ImportError("This framework is not installed.")


try:
    from fastopenapi.routers.aiohttp.async_router import AioHttpRouter
except ModuleNotFoundError:
    AioHttpRouter = MissingRouter

try:
    from fastopenapi.routers.falcon.async_router import FalconAsyncRouter
    from fastopenapi.routers.falcon.sync_router import FalconRouter
except ModuleNotFoundError:
    FalconRouter = MissingRouter
    FalconAsyncRouter = MissingRouter

try:
    from fastopenapi.routers.flask.sync_router import FlaskRouter
except ModuleNotFoundError:
    FlaskRouter = MissingRouter

try:
    from fastopenapi.routers.quart.async_router import QuartRouter
except ModuleNotFoundError:
    QuartRouter = MissingRouter

try:
    from fastopenapi.routers.sanic.async_router import SanicRouter
except ModuleNotFoundError:
    SanicRouter = MissingRouter

try:
    from fastopenapi.routers.starlette.async_router import StarletteRouter
except ModuleNotFoundError:
    StarletteRouter = MissingRouter

try:
    from fastopenapi.routers.tornado.async_router import TornadoRouter
except ModuleNotFoundError:
    TornadoRouter = MissingRouter

try:
    from fastopenapi.routers.django.async_router import DjangoAsyncRouter
    from fastopenapi.routers.django.sync_router import DjangoRouter
except ModuleNotFoundError:
    DjangoRouter = MissingRouter
    DjangoAsyncRouter = MissingRouter

__all__ = [
    "AioHttpRouter",
    "FalconRouter",
    "FalconAsyncRouter",
    "FlaskRouter",
    "QuartRouter",
    "SanicRouter",
    "StarletteRouter",
    "TornadoRouter",
    "DjangoRouter",
    "DjangoAsyncRouter",
]
