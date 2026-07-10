"""Unified test clients for the cross-framework integration matrix.

Each wrapper adapts one framework's canonical test client to a single
interface: ``send(method, path, headers, body) -> ClientResponse``.
Everything else (query strings, cookies, JSON/form/multipart encoding)
is done framework-agnostically in ``BaseClient.request``.

Framework imports live in the wrapper constructors on purpose: a missing
optional dependency must surface as ImportError from the factory (turned
into a pytest skip) without breaking import of this module for the other
variants.
"""

import asyncio
import itertools
import json as _json
import sys
import types
from abc import ABC, abstractmethod
from typing import Any
from urllib.parse import urlencode

from tests.integration.apps import register_routes
from tests.integration.utils import ensure_policy_event_loop

_MISSING = object()


class ClientResponse:
    def __init__(self, status: int, headers: Any, body: bytes):
        self.status = int(status)
        # accept dict or iterable of (name, value); keep last value per name
        items = headers.items() if hasattr(headers, "items") else headers
        self.headers = {str(k).lower(): str(v) for k, v in items}
        self.body = bytes(body) if body else b""

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")

    def json(self) -> Any:
        return _json.loads(self.body)


class BaseClient(ABC):
    framework: str = ""

    @abstractmethod
    def send(
        self, method: str, path: str, headers: dict[str, str], body: bytes | None
    ) -> ClientResponse: ...

    def close(self) -> None:
        pass

    def request(
        self,
        method: str,
        path: str,
        *,
        query: list[tuple[str, str]] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        json_body: Any = _MISSING,
        content: bytes | None = None,
        content_type: str | None = None,
    ) -> ClientResponse:
        full_path = path
        if query:
            full_path = f"{path}?{urlencode(query)}"

        hdrs = dict(headers or {})
        if cookies:
            hdrs["Cookie"] = "; ".join(f"{k}={v}" for k, v in cookies.items())

        body: bytes | None = None
        if json_body is not _MISSING:
            body = _json.dumps(json_body).encode()
            hdrs.setdefault("Content-Type", "application/json")
        if content is not None:
            body = content
        if content_type is not None:
            hdrs["Content-Type"] = content_type

        return self.send(method.upper(), full_path, hdrs, body)

    def get(self, path: str, **kw: Any) -> ClientResponse:
        return self.request("GET", path, **kw)

    def post(self, path: str, **kw: Any) -> ClientResponse:
        return self.request("POST", path, **kw)

    def put(self, path: str, **kw: Any) -> ClientResponse:
        return self.request("PUT", path, **kw)

    def patch(self, path: str, **kw: Any) -> ClientResponse:
        return self.request("PATCH", path, **kw)

    def delete(self, path: str, **kw: Any) -> ClientResponse:
        return self.request("DELETE", path, **kw)

    def head(self, path: str, **kw: Any) -> ClientResponse:
        return self.request("HEAD", path, **kw)

    def options(self, path: str, **kw: Any) -> ClientResponse:
        return self.request("OPTIONS", path, **kw)


# ---------------------------------------------------------------------------
# WSGI family
# ---------------------------------------------------------------------------


class FlaskClient(BaseClient):
    framework = "flask"

    def __init__(self):
        from flask import Flask

        from fastopenapi.routers import FlaskRouter

        app = Flask("fastopenapi_itest_flask")
        router = FlaskRouter(app=app)
        register_routes(router)
        self._client = app.test_client()

    def send(self, method, path, headers, body):
        hdrs = dict(headers)
        # werkzeug's test client overrides the Cookie header with its own jar
        cookie_header = hdrs.pop("Cookie", None)
        if cookie_header:
            for pair in cookie_header.split("; "):
                name, _, value = pair.partition("=")
                self._client.set_cookie(name, value)
        resp = self._client.open(
            path, method=method, headers=list(hdrs.items()), data=body
        )
        return ClientResponse(resp.status_code, resp.headers.items(), resp.get_data())


class QuartClient(BaseClient):
    framework = "quart"

    def __init__(self):
        from quart import Quart

        from fastopenapi.routers import QuartRouter

        app = Quart("fastopenapi_itest_quart")
        router = QuartRouter(app=app)
        register_routes(router)
        self._app = app

    def send(self, method, path, headers, body):
        async def go():
            client = self._app.test_client()
            resp = await client.open(path, method=method, headers=headers, data=body)
            data = await resp.get_data()
            return resp, data

        resp, data = asyncio.run(go())
        return ClientResponse(resp.status_code, resp.headers.items(), data)


class DjangoClientBase(BaseClient):
    """Common Django plumbing: an isolated URLconf module per variant."""

    router_cls_name = ""
    urlconf_name = ""

    def __init__(self):
        from django.conf import settings
        from django.test.utils import override_settings
        from django.urls import path as django_path

        import fastopenapi.routers as fo_routers

        if not settings.configured:
            settings.configure(ROOT_URLCONF=self.urlconf_name, ALLOWED_HOSTS=["*"])

        router_cls = getattr(fo_routers, self.router_cls_name)
        router = router_cls(app=True)
        register_routes(router)

        module = types.ModuleType(self.urlconf_name)
        module.urlpatterns = [django_path("", router.urls)]
        sys.modules[self.urlconf_name] = module

        self._override_settings = override_settings

    @staticmethod
    def _finish(result):
        return result

    def send(self, method, path, headers, body):
        hdrs = dict(headers)
        content_type = hdrs.pop("Content-Type", "application/octet-stream")
        # the test client merges a Cookie header with its own; use the jar
        cookie_header = hdrs.pop("Cookie", None)
        client = self._client_cls()
        if cookie_header:
            for pair in cookie_header.split("; "):
                name, _, value = pair.partition("=")
                client.cookies[name] = value
        with self._override_settings(ROOT_URLCONF=self.urlconf_name):
            resp = self._finish(
                client.generic(
                    method,
                    path,
                    data=body or b"",
                    content_type=content_type,
                    headers=hdrs,
                )
            )
        return ClientResponse(resp.status_code, resp.headers.items(), resp.content)


class DjangoSyncClient(DjangoClientBase):
    framework = "django"
    router_cls_name = "DjangoRouter"
    urlconf_name = "fastopenapi_itest_django_sync_urls"

    def __init__(self):
        super().__init__()
        from django.test import Client

        self._client_cls = Client


class DjangoAsyncClient(DjangoClientBase):
    framework = "django-async"
    router_cls_name = "DjangoAsyncRouter"
    urlconf_name = "fastopenapi_itest_django_async_urls"

    _finish = staticmethod(asyncio.run)

    def __init__(self):
        super().__init__()
        from django.test import AsyncClient

        self._client_cls = AsyncClient


class FalconSyncClient(BaseClient):
    framework = "falcon"

    def __init__(self):
        import falcon
        import falcon.testing

        from fastopenapi.routers import FalconRouter

        app = falcon.App()
        router = FalconRouter(app=app)
        register_routes(router)
        self._client = falcon.testing.TestClient(app)

    def send(self, method, path, headers, body):
        path, _, qs = path.partition("?")
        result = self._client.simulate_request(
            method=method, path=path, query_string=qs, headers=headers, body=body
        )
        return ClientResponse(
            result.status_code, result.headers.items(), result.content
        )


class FalconAsyncClient(BaseClient):
    framework = "falcon-async"

    def __init__(self):
        import falcon.asgi
        import falcon.testing

        from fastopenapi.routers import FalconAsyncRouter

        app = falcon.asgi.App()
        router = FalconAsyncRouter(app=app)
        register_routes(router)
        self._client = falcon.testing.TestClient(app)

    def send(self, method, path, headers, body):
        path, _, qs = path.partition("?")
        # WORKAROUND: falcon's async_to_sync on py<3.11 needs a policy loop;
        # see ensure_policy_event_loop in tests/integration/utils.py.
        ensure_policy_event_loop()
        result = self._client.simulate_request(
            method=method, path=path, query_string=qs, headers=headers, body=body
        )
        return ClientResponse(
            result.status_code, result.headers.items(), result.content
        )


# ---------------------------------------------------------------------------
# ASGI / async family
# ---------------------------------------------------------------------------


class StarletteClient(BaseClient):
    framework = "starlette"

    def __init__(self):
        from starlette.applications import Starlette
        from starlette.testclient import TestClient

        from fastopenapi.routers import StarletteRouter

        app = Starlette()
        router = StarletteRouter(app=app)
        register_routes(router)
        self._client = TestClient(app, raise_server_exceptions=False)

    def send(self, method, path, headers, body):
        resp = self._client.request(method, path, headers=headers, content=body)
        return ClientResponse(resp.status_code, resp.headers.items(), resp.content)

    def close(self):
        self._client.close()


class AioHttpClient(BaseClient):
    framework = "aiohttp"

    def __init__(self):
        from aiohttp import web
        from aiohttp.test_utils import TestClient as AioTestClient
        from aiohttp.test_utils import TestServer

        from fastopenapi.routers import AioHttpRouter

        self._loop = asyncio.new_event_loop()
        app = web.Application()
        router = AioHttpRouter(app=app)
        register_routes(router)
        self._server = TestServer(app, loop=self._loop)
        self._client = AioTestClient(self._server, loop=self._loop)
        self._loop.run_until_complete(self._client.start_server())

    def send(self, method, path, headers, body):
        async def go():
            resp = await self._client.request(method, path, headers=headers, data=body)
            raw = await resp.read()
            return resp, raw

        resp, raw = self._loop.run_until_complete(go())
        return ClientResponse(resp.status, resp.headers.items(), raw)

    def close(self):
        self._loop.run_until_complete(self._client.close())
        self._loop.close()


_sanic_counter = itertools.count()


class SanicClient(BaseClient):
    framework = "sanic"

    def __init__(self):
        from sanic import Sanic
        from sanic_testing.testing import SanicASGITestClient

        from fastopenapi.routers import SanicRouter

        Sanic.test_mode = True
        app = Sanic(f"fastopenapi_itest_sanic_{next(_sanic_counter)}")
        router = SanicRouter(app=app)
        register_routes(router)
        self._app = app
        self._client_cls = SanicASGITestClient

    def send(self, method, path, headers, body):
        async def go():
            client = self._client_cls(self._app)
            kwargs = {"headers": headers}
            if body is not None:
                kwargs["content"] = body
            _, resp = await client.request(method, path, **kwargs)
            return resp

        resp = asyncio.run(go())
        return ClientResponse(resp.status_code, resp.headers.items(), resp.content)


class TornadoClient(BaseClient):
    framework = "tornado"

    def __init__(self):
        from tornado.httpclient import AsyncHTTPClient, HTTPRequest
        from tornado.httpserver import HTTPServer
        from tornado.testing import bind_unused_port
        from tornado.web import Application

        from fastopenapi.routers import TornadoRouter

        self._http_client_cls = AsyncHTTPClient
        self._http_request_cls = HTTPRequest

        self._loop = asyncio.new_event_loop()
        app = Application()
        router = TornadoRouter(app=app)
        register_routes(router)

        sock, self._port = bind_unused_port()

        async def _start():
            self._server = HTTPServer(app)
            self._server.add_sockets([sock])

        self._loop.run_until_complete(_start())

    def send(self, method, path, headers, body):
        async def go():
            client = self._http_client_cls()
            req = self._http_request_cls(
                f"http://127.0.0.1:{self._port}{path}",
                method=method,
                headers=headers,
                body=body,
                allow_nonstandard_methods=True,
            )
            return await client.fetch(req, raise_error=False)

        resp = self._loop.run_until_complete(go())
        return ClientResponse(resp.code, resp.headers.get_all(), resp.body or b"")

    def close(self):
        async def _stop():
            self._server.stop()
            await self._server.close_all_connections()

        self._loop.run_until_complete(_stop())
        self._loop.close()


CLIENT_FACTORIES: dict[str, type[BaseClient]] = {
    "flask": FlaskClient,
    "quart": QuartClient,
    "starlette": StarletteClient,
    "aiohttp": AioHttpClient,
    "sanic": SanicClient,
    "tornado": TornadoClient,
    "falcon": FalconSyncClient,
    "falcon-async": FalconAsyncClient,
    "django": DjangoSyncClient,
    "django-async": DjangoAsyncClient,
}
