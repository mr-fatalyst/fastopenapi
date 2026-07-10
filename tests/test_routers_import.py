import builtins
import importlib
import sys

import pytest

FRAMEWORKS = {
    "aiohttp",
    "falcon",
    "flask",
    "quart",
    "sanic",
    "starlette",
    "tornado",
    "django",
}


class TestFastOpenAPIRouters:
    @pytest.fixture(autouse=True)
    def restore_sys_modules(self, monkeypatch):
        # Store the original import function
        self.original_import = builtins.__import__
        yield
        monkeypatch.undo()
        # The test re-imported the package, so the module object in
        # sys.modules and the parent-package attribute may disagree.
        # Drop it and import fresh under real imports so later tests
        # see the real router classes again
        sys.modules.pop("fastopenapi.routers", None)
        importlib.import_module("fastopenapi.routers")

    def _purge_modules(self, monkeypatch, roots):
        """Drop cached modules so imports go through __import__ again"""
        for mod in list(sys.modules):
            if mod == "fastopenapi.routers" or mod.startswith("fastopenapi.routers."):
                monkeypatch.delitem(sys.modules, mod, raising=False)
            elif mod.split(".")[0] in roots:
                monkeypatch.delitem(sys.modules, mod, raising=False)

    def test_all_missing(self, monkeypatch):
        """Absent frameworks map to MissingRouter with an install hint"""
        self._purge_modules(monkeypatch, FRAMEWORKS)

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name.split(".")[0] in FRAMEWORKS:
                raise ModuleNotFoundError(f"No module named '{name}'", name=name)
            return self.original_import(name, globals, locals, fromlist, level)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        import fastopenapi.routers as routers

        importlib.reload(routers)
        from fastopenapi.routers import MissingRouter

        assert issubclass(routers.AioHttpRouter, MissingRouter)
        assert issubclass(routers.FalconRouter, MissingRouter)
        assert issubclass(routers.FalconAsyncRouter, MissingRouter)
        assert issubclass(routers.FlaskRouter, MissingRouter)
        assert issubclass(routers.QuartRouter, MissingRouter)
        assert issubclass(routers.SanicRouter, MissingRouter)
        assert issubclass(routers.StarletteRouter, MissingRouter)
        assert issubclass(routers.TornadoRouter, MissingRouter)
        assert issubclass(routers.DjangoRouter, MissingRouter)
        assert issubclass(routers.DjangoAsyncRouter, MissingRouter)

        with pytest.raises(
            ImportError,
            match=r"Falcon is not installed. Try: pip install fastopenapi\[falcon\]",
        ):
            routers.FalconRouter()

    def test_transitive_import_error_not_masked(self, monkeypatch):
        """A broken import chain of an installed framework surfaces its real
        error instead of a misleading 'not installed' hint"""
        self._purge_modules(monkeypatch, set())

        broken = "fastopenapi.routers.flask.extractors"

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == broken:
                raise ModuleNotFoundError(f"No module named '{name}'", name=name)
            return self.original_import(name, globals, locals, fromlist, level)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        import fastopenapi.routers as routers

        importlib.reload(routers)
        from fastopenapi.routers import MissingRouter

        assert issubclass(routers.FlaskRouter, MissingRouter)
        with pytest.raises(ImportError, match=r"Flask import failed.*extractors"):
            routers.FlaskRouter()
        # Other frameworks are untouched
        assert not issubclass(routers.StarletteRouter, MissingRouter)

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
