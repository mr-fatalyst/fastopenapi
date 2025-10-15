import warnings


def test_error_handler_warns(monkeypatch):
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        import importlib

        importlib.reload(__import__("fastopenapi.error_handler"))

        assert any(isinstance(x.message, DeprecationWarning) for x in w)
        assert any("fastopenapi.error_handler" in str(x.message) for x in w)
