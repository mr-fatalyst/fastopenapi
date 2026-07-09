"""Docs endpoints are optional: docs_url/redoc_url can be disabled."""

import itertools

_counter = itertools.count()


class TestDocsUrlsDisabled:
    def test_flask(self):
        from flask import Flask

        from fastopenapi.routers import FlaskRouter

        app = Flask(f"docs_off_{next(_counter)}")
        FlaskRouter(app=app, docs_url=None, redoc_url=None)

        rules = {rule.rule for rule in app.url_map.iter_rules()}
        assert "/openapi.json" in rules
        assert "/docs" not in rules
        assert "/redoc" not in rules

    def test_quart(self):
        from quart import Quart

        from fastopenapi.routers import QuartRouter

        app = Quart(f"docs_off_{next(_counter)}")
        QuartRouter(app=app, docs_url=None, redoc_url=None)

        rules = {rule.rule for rule in app.url_map.iter_rules()}
        assert "/openapi.json" in rules
        assert "/docs" not in rules

    def test_starlette(self):
        from starlette.applications import Starlette

        from fastopenapi.routers import StarletteRouter

        app = Starlette()
        StarletteRouter(app=app, docs_url=None, redoc_url=None)

        paths = {route.path for route in app.router.routes}
        assert "/openapi.json" in paths
        assert "/docs" not in paths

    def test_aiohttp(self):
        from aiohttp import web

        from fastopenapi.routers import AioHttpRouter

        app = web.Application()
        AioHttpRouter(app=app, docs_url=None, redoc_url=None)

        paths = {route.resource.get_info().get("path") for route in app.router.routes()}
        assert "/openapi.json" in paths
        assert "/docs" not in paths

    def test_sanic(self):
        from sanic import Sanic

        from fastopenapi.routers import SanicRouter

        Sanic.test_mode = True
        app = Sanic(f"docs_off_{next(_counter)}")
        SanicRouter(app=app, docs_url=None, redoc_url=None)

        paths = {route.path for route in app.router.routes}
        assert not any("docs" in path for path in paths)

    def test_tornado(self):
        from tornado.web import Application

        from fastopenapi.routers import TornadoRouter

        app = Application()
        router = TornadoRouter(app=app, docs_url=None, redoc_url=None)

        names = {spec.name for spec in router.routes}
        assert "openapi-schema" in names
        assert "swagger-ui" not in names
        assert "redoc-ui" not in names

    def test_falcon_sync(self):
        from falcon import App

        from fastopenapi.routers import FalconRouter

        FalconRouter(app=App(), docs_url=None, redoc_url=None)

    def test_falcon_async(self):
        import falcon.asgi

        from fastopenapi.routers import FalconAsyncRouter

        FalconAsyncRouter(app=falcon.asgi.App(), docs_url=None, redoc_url=None)

    def test_django_sync(self):
        from fastopenapi.routers import DjangoRouter

        router = DjangoRouter(app=True, docs_url=None, redoc_url=None)

        assert "/openapi.json" in router._views
        assert "/docs" not in router._views

    def test_django_async(self):
        from fastopenapi.routers import DjangoAsyncRouter

        router = DjangoAsyncRouter(app=True, docs_url=None, redoc_url=None)

        assert "/openapi.json" in router._views
        assert "/docs" not in router._views


class TestDjangoRegisterDocsFlag:
    def test_register_docs_true(self):
        from fastopenapi.routers import DjangoRouter

        router = DjangoRouter(register_docs=True)

        assert "/openapi.json" in router._views

    def test_register_docs_false(self):
        from fastopenapi.routers import DjangoRouter

        router = DjangoRouter(register_docs=False)

        assert router._views == {}
        assert router.app is None


class TestDocsNoopWithoutOpenapiUrl:
    """_register_docs_endpoints is a no-op when openapi_url is disabled"""

    def test_all_routers_return_early(self):
        from fastopenapi.routers import (
            AioHttpRouter,
            DjangoAsyncRouter,
            DjangoRouter,
            FalconAsyncRouter,
            FalconRouter,
            FlaskRouter,
            QuartRouter,
            SanicRouter,
            StarletteRouter,
            TornadoRouter,
        )

        router_classes = [
            AioHttpRouter,
            DjangoAsyncRouter,
            DjangoRouter,
            FalconAsyncRouter,
            FalconRouter,
            FlaskRouter,
            QuartRouter,
            SanicRouter,
            StarletteRouter,
            TornadoRouter,
        ]
        for router_cls in router_classes:
            # no app, no openapi_url: registration must not touch anything
            router = router_cls(openapi_url=None)

            assert router._register_docs_endpoints() is None
