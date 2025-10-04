import functools
from collections.abc import Callable

from aiohttp import web

from fastopenapi.core.types import Response
from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui
from fastopenapi.routers.aiohttp.extractors import AioHttpRequestDataExtractor
from fastopenapi.routers.base import BaseAdapter
from fastopenapi.routers.common import RequestEnvelope


class AioHttpRouter(BaseAdapter):
    """AioHttp adapter for FastOpenAPI"""

    extractor_async_cls = AioHttpRequestDataExtractor

    def __init__(self, app: web.Application = None, **kwargs):
        super().__init__(app, **kwargs)

    def add_route(self, path: str, method: str, endpoint: Callable):
        """Add route to AioHttp application"""
        super().add_route(path, method, endpoint)

        if self.app is not None:
            view = functools.partial(self._aiohttp_view, router=self, endpoint=endpoint)
            self.app.router.add_route(method.upper(), path, view)

    @staticmethod
    async def _aiohttp_view(request: web.Request, router, endpoint: Callable):
        """Handle AioHttp request"""
        env = RequestEnvelope(request=request, path_params=None)
        return await router.handle_request_async(endpoint, env)

    def build_framework_response(self, response: Response) -> web.Response:
        """Build AioHttp response"""
        content_type = response.headers.get("Content-Type", "application/json")

        # Binary content
        if isinstance(response.content, bytes):
            return web.Response(
                body=response.content,
                status=response.status_code,
                headers={**response.headers, "Content-Type": content_type},
            )

        # String non-JSON content (CSV, XML, plain text, etc.)
        if isinstance(response.content, str) and content_type not in [
            "application/json",
            "text/json",
        ]:
            return web.Response(
                text=response.content,
                status=response.status_code,
                headers={**response.headers, "Content-Type": content_type},
            )

        # JSON content (dict, list, None)
        return web.json_response(
            response.content, status=response.status_code, headers=response.headers
        )

    def is_framework_response(self, response: Response | web.Response) -> bool:
        return isinstance(response, web.Response)

    def _register_docs_endpoints(self):
        """Register documentation endpoints"""

        async def openapi_view(request):
            return web.json_response(self.openapi)

        async def docs_view(request):
            html = render_swagger_ui(self.openapi_url)
            return web.Response(text=html, content_type="text/html")

        async def redoc_view(request):
            html = render_redoc_ui(self.openapi_url)
            return web.Response(text=html, content_type="text/html")

        if self.app is not None:
            self.app.router.add_route("GET", self.openapi_url, openapi_view)
            self.app.router.add_route("GET", self.docs_url, docs_view)
            self.app.router.add_route("GET", self.redoc_url, redoc_view)
