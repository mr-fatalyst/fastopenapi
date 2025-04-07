class MissingRouter:
    def __init__(self, *args, **kwargs):
        raise ImportError("This framework is not installed.")


try:
    from fastopenapi.routers.aiohttp import AioHttpRouter
except ModuleNotFoundError:
    AioHttpRouter = MissingRouter

try:
    from fastopenapi.routers.falcon import FalconRouter
except ModuleNotFoundError:
    FalconRouter = MissingRouter

try:
    from fastopenapi.routers.flask import FlaskRouter
except ModuleNotFoundError:
    FlaskRouter = MissingRouter

try:
    from fastopenapi.routers.quart import QuartRouter
except ModuleNotFoundError:
    QuartRouter = MissingRouter

try:
    from fastopenapi.routers.sanic import SanicRouter
except ModuleNotFoundError:
    SanicRouter = MissingRouter

try:
    from fastopenapi.routers.starlette import StarletteRouter
except ModuleNotFoundError:
    StarletteRouter = MissingRouter

try:
    from fastopenapi.routers.tornado import TornadoRouter
except ModuleNotFoundError:
    TornadoRouter = MissingRouter

__all__ = [
    "AioHttpRouter",
    "FalconRouter",
    "FlaskRouter",
    "QuartRouter",
    "SanicRouter",
    "StarletteRouter",
    "TornadoRouter",
]
