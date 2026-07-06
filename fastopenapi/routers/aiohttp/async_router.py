import functools
from collections.abc import Callable
from typing import Any

from aiohttp import web

from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui
from fastopenapi.response.serializer import WireResponse
from fastopenapi.routers.aiohttp.extractors import AioHttpRequestDataExtractor
from fastopenapi.routers.base import BaseAdapter
from fastopenapi.routers.common import RequestEnvelope


class AioHttpRouter(BaseAdapter):
    """AioHttp adapter for FastOpenAPI"""

    extractor_async_cls = AioHttpRequestDataExtractor

    def __init__(self, app: web.Application | None = None, **kwargs: Any):
        self._explicit_head_paths: set[str] = set()
        self._auto_head_paths: set[str] = set()
        super().__init__(app, **kwargs)

    def add_route(self, path: str, method: str, endpoint: Callable[..., Any]) -> None:
        """Add route to AioHttp application"""
        super().add_route(path, method, endpoint)

        if self.app is not None:
            method = method.upper()
            if method == "HEAD" and path in self._auto_head_paths:
                raise TypeError(
                    f"Explicit HEAD route for '{path}' must be registered "
                    f"before its GET route (auto-HEAD is already in place)"
                )
            view = functools.partial(self._aiohttp_view, router=self, endpoint=endpoint)
            self.app.router.add_route(method, path, view)
            if method == "HEAD":
                self._explicit_head_paths.add(path)
            elif method == "GET" and path not in self._explicit_head_paths:
                # aiohttp itself omits the body for HEAD responses
                self.app.router.add_route("HEAD", path, view)
                self._auto_head_paths.add(path)

    @staticmethod
    async def _aiohttp_view(
        request: web.Request, router: Any, endpoint: Callable[..., Any]
    ) -> Any:
        """Handle AioHttp request"""
        env = RequestEnvelope(request=request, path_params=None)
        return await router.handle_request_async(endpoint, env)

    def build_framework_response(self, response: WireResponse) -> web.Response:
        """Wrap the finalized triple into an aiohttp response"""
        return web.Response(
            body=response.body,
            status=response.status,
            headers=response.headers,
        )

    def is_framework_response(self, response: Any) -> bool:
        # StreamResponse covers web.Response, FileResponse and streaming
        return isinstance(response, web.StreamResponse)

    def _register_docs_endpoints(self) -> None:
        """Register documentation endpoints"""
        openapi_url = self.openapi_url
        if openapi_url is None:
            return

        async def openapi_view(request: web.Request) -> web.Response:
            return web.json_response(self.openapi)

        async def docs_view(request: web.Request) -> web.Response:
            html = render_swagger_ui(openapi_url)
            return web.Response(text=html, content_type="text/html")

        async def redoc_view(request: web.Request) -> web.Response:
            html = render_redoc_ui(openapi_url)
            return web.Response(text=html, content_type="text/html")

        if self.app is not None:
            self.app.router.add_route("GET", openapi_url, openapi_view)
            if self.docs_url:
                self.app.router.add_route("GET", self.docs_url, docs_view)
            if self.redoc_url:
                self.app.router.add_route("GET", self.redoc_url, redoc_view)
