import builtins
import importlib

import pytest


class TestFastOpenAPIRouters:
    @pytest.fixture(autouse=True)
    def restore_sys_modules(self, monkeypatch):
        # Store the original import function
        self.original_import = builtins.__import__
        yield
        monkeypatch.undo()

    def test_all_missing(self, monkeypatch):
        modules_to_fail = {
            "fastopenapi.routers.aiohttp.async_router",
            "fastopenapi.routers.falcon.sync_router",
            "fastopenapi.routers.falcon.async_router",
            "fastopenapi.routers.flask.sync_router",
            "fastopenapi.routers.quart.async_router",
            "fastopenapi.routers.sanic.async_router",
            "fastopenapi.routers.starlette.async_router",
            "fastopenapi.routers.tornado.async_router",
            "fastopenapi.routers.django.sync_router",
            "fastopenapi.routers.django.async_router",
        }

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name in modules_to_fail:
                raise ModuleNotFoundError(f"No module named '{name}'")
            return self.original_import(name, globals, locals, fromlist, level)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        import fastopenapi.routers as routers

        importlib.reload(routers)
        from fastopenapi.routers import MissingRouter

        assert routers.AioHttpRouter is MissingRouter
        assert routers.FalconRouter is MissingRouter
        assert routers.FalconAsyncRouter is MissingRouter
        assert routers.FlaskRouter is MissingRouter
        assert routers.QuartRouter is MissingRouter
        assert routers.SanicRouter is MissingRouter
        assert routers.StarletteRouter is MissingRouter
        assert routers.TornadoRouter is MissingRouter
        assert routers.DjangoRouter is MissingRouter
        assert routers.DjangoAsyncRouter is MissingRouter

        with pytest.raises(ImportError, match="This framework is not installed."):
            routers.FalconRouter()

    def test_all_variable(self):
        import fastopenapi.routers as routers

        expected = [
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
        assert routers.__all__ == expected
