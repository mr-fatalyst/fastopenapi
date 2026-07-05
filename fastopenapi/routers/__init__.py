from typing import Any


class MissingRouter:
    """Placeholder that says which framework (and extra) is missing"""

    framework = "This framework"
    extra: str | None = None

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        hint = f" Try: pip install fastopenapi[{self.extra}]" if self.extra else ""
        raise ImportError(f"{self.framework} is not installed.{hint}")


def _missing_router(framework: str, extra: str) -> type[MissingRouter]:
    return type(
        f"Missing{framework}Router",
        (MissingRouter,),
        {"framework": framework, "extra": extra},
    )


try:
    from fastopenapi.routers.aiohttp.async_router import AioHttpRouter
except ModuleNotFoundError:
    AioHttpRouter = _missing_router("aiohttp", "aiohttp")

try:
    from fastopenapi.routers.falcon.async_router import FalconAsyncRouter
    from fastopenapi.routers.falcon.sync_router import FalconRouter
except ModuleNotFoundError:
    FalconRouter = _missing_router("Falcon", "falcon")
    FalconAsyncRouter = _missing_router("Falcon", "falcon")

try:
    from fastopenapi.routers.flask.sync_router import FlaskRouter
except ModuleNotFoundError:
    FlaskRouter = _missing_router("Flask", "flask")

try:
    from fastopenapi.routers.quart.async_router import QuartRouter
except ModuleNotFoundError:
    QuartRouter = _missing_router("Quart", "quart")

try:
    from fastopenapi.routers.sanic.async_router import SanicRouter
except ModuleNotFoundError:
    SanicRouter = _missing_router("Sanic", "sanic")

try:
    from fastopenapi.routers.starlette.async_router import StarletteRouter
except ModuleNotFoundError:
    StarletteRouter = _missing_router("Starlette", "starlette")

try:
    from fastopenapi.routers.tornado.async_router import TornadoRouter
except ModuleNotFoundError:
    TornadoRouter = _missing_router("Tornado", "tornado")

try:
    from fastopenapi.routers.django.async_router import DjangoAsyncRouter
    from fastopenapi.routers.django.sync_router import DjangoRouter
except ModuleNotFoundError:
    DjangoRouter = _missing_router("Django", "django")
    DjangoAsyncRouter = _missing_router("Django", "django")

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
