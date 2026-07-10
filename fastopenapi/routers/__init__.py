from typing import TYPE_CHECKING, Any


class MissingRouter:
    """Placeholder that says which framework (and extra) is missing"""

    framework = "This framework"
    extra: str | None = None
    # Set when the framework package is present but its import chain broke
    # (transitive dependency, internal bug) — the real error must surface
    # instead of a misleading "not installed" hint
    reason: str | None = None

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if self.reason:
            raise ImportError(f"{self.framework} import failed: {self.reason}")
        hint = f" Try: pip install fastopenapi[{self.extra}]" if self.extra else ""
        raise ImportError(f"{self.framework} is not installed.{hint}")


def _missing_router(
    framework: str, extra: str, exc: ModuleNotFoundError
) -> type[MissingRouter]:
    module_root = (exc.name or "").split(".")[0]
    reason = None if module_root == extra else str(exc)
    return type(
        f"Missing{framework}Router",
        (MissingRouter,),
        {"framework": framework, "extra": extra, "reason": reason},
    )


if TYPE_CHECKING:  # noqa: C901 mccabe counts the fallback chain as branches
    # mypy always sees the real router types; the runtime fallbacks below
    # replace them with MissingRouter when a framework extra is absent
    from fastopenapi.routers.aiohttp.async_router import AioHttpRouter
    from fastopenapi.routers.django.async_router import DjangoAsyncRouter
    from fastopenapi.routers.django.sync_router import DjangoRouter
    from fastopenapi.routers.falcon.async_router import FalconAsyncRouter
    from fastopenapi.routers.falcon.sync_router import FalconRouter
    from fastopenapi.routers.flask.sync_router import FlaskRouter
    from fastopenapi.routers.quart.async_router import QuartRouter
    from fastopenapi.routers.sanic.async_router import SanicRouter
    from fastopenapi.routers.starlette.async_router import StarletteRouter
    from fastopenapi.routers.tornado.async_router import TornadoRouter
else:
    try:
        from fastopenapi.routers.aiohttp.async_router import AioHttpRouter
    except ModuleNotFoundError as e:
        AioHttpRouter = _missing_router("aiohttp", "aiohttp", e)

    try:
        from fastopenapi.routers.falcon.async_router import FalconAsyncRouter
        from fastopenapi.routers.falcon.sync_router import FalconRouter
    except ModuleNotFoundError as e:
        FalconRouter = _missing_router("Falcon", "falcon", e)
        FalconAsyncRouter = _missing_router("Falcon", "falcon", e)

    try:
        from fastopenapi.routers.flask.sync_router import FlaskRouter
    except ModuleNotFoundError as e:
        FlaskRouter = _missing_router("Flask", "flask", e)

    try:
        from fastopenapi.routers.quart.async_router import QuartRouter
    except ModuleNotFoundError as e:
        QuartRouter = _missing_router("Quart", "quart", e)

    try:
        from fastopenapi.routers.sanic.async_router import SanicRouter
    except ModuleNotFoundError as e:
        SanicRouter = _missing_router("Sanic", "sanic", e)

    try:
        from fastopenapi.routers.starlette.async_router import StarletteRouter
    except ModuleNotFoundError as e:
        StarletteRouter = _missing_router("Starlette", "starlette", e)

    try:
        from fastopenapi.routers.tornado.async_router import TornadoRouter
    except ModuleNotFoundError as e:
        TornadoRouter = _missing_router("Tornado", "tornado", e)

    try:
        from fastopenapi.routers.django.async_router import DjangoAsyncRouter
        from fastopenapi.routers.django.sync_router import DjangoRouter
    except ModuleNotFoundError as e:
        DjangoRouter = _missing_router("Django", "django", e)
        DjangoAsyncRouter = _missing_router("Django", "django", e)

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
