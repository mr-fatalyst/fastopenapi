import builtins
import importlib

import pytest


@pytest.fixture(autouse=True)
def restore_sys_modules(monkeypatch):
    builtins.__import__
    yield
    monkeypatch.undo()


def test_all_missing(monkeypatch):
    modules_to_fail = {
        "fastopenapi.routers.falcon",
        "fastopenapi.routers.flask",
        "fastopenapi.routers.quart",
        "fastopenapi.routers.sanic",
        "fastopenapi.routers.starlette",
        "fastopenapi.routers.tornado",
    }
    orig_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name in modules_to_fail:
            raise ModuleNotFoundError(f"No module named '{name}'")
        return orig_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    import fastopenapi.routers as routers

    importlib.reload(routers)
    from fastopenapi.routers import MissingRouter

    assert routers.FalconRouter is MissingRouter
    assert routers.FlaskRouter is MissingRouter
    assert routers.QuartRouter is MissingRouter
    assert routers.SanicRouter is MissingRouter
    assert routers.StarletteRouter is MissingRouter
    assert routers.TornadoRouter is MissingRouter

    with pytest.raises(ImportError, match="This framework is not installed."):
        routers.FalconRouter()


def test_all_variable():
    import fastopenapi.routers as routers

    expected = [
        "FalconRouter",
        "FlaskRouter",
        "QuartRouter",
        "SanicRouter",
        "StarletteRouter",
        "TornadoRouter",
    ]
    assert routers.__all__ == expected
