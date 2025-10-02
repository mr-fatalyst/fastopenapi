import functools
from collections.abc import Callable

from starlette.applications import Starlette
from starlette.responses import (
    HTMLResponse,
    JSONResponse,
)
from starlette.responses import Response as StarletteResponse
from starlette.routing import Route

from fastopenapi.core.types import Response
from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui
from fastopenapi.routers.base import BaseAdapter
from fastopenapi.routers.common import RequestEnvelope
from fastopenapi.routers.starlette.extractors import StarletteRequestDataExtractor


class StarletteRouter(BaseAdapter):
    """Starlette adapter for FastOpenAPI"""

    extractor_async_cls = StarletteRequestDataExtractor

    def __init__(self, app: Starlette = None, **kwargs):
        self._routes_starlette = []
        super().__init__(app, **kwargs)

    def add_route(self, path: str, method: str, endpoint: Callable):
        """Add route to Starlette application"""
        super().add_route(path, method, endpoint)

        view = functools.partial(self._starlette_view, router=self, endpoint=endpoint)
        route = Route(path, view, methods=[method.upper()])

        if self.app is not None:
            self.app.router.routes.append(route)
        else:
            self._routes_starlette.append(route)

    @staticmethod
    async def _starlette_view(request, router, endpoint):
        """Handle Starlette request"""
        env = RequestEnvelope(request=request, path_params=None)
        return await router.handle_request_async(endpoint, env)

    def build_framework_response(self, response: Response) -> JSONResponse:
        """Build Starlette response"""
        return JSONResponse(
            response.content, status_code=response.status_code, headers=response.headers
        )

    def is_framework_response(self, response: Response | StarletteResponse) -> bool:
        return isinstance(response, StarletteResponse)

    def _register_docs_endpoints(self):
        """Register documentation endpoints"""

        async def openapi_view(request):
            return JSONResponse(self.openapi)

        async def docs_view(request):
            html = render_swagger_ui(self.openapi_url)
            return HTMLResponse(html)

        async def redoc_view(request):
            html = render_redoc_ui(self.openapi_url)
            return HTMLResponse(html)

        self.app.router.routes.append(
            Route(self.openapi_url, openapi_view, methods=["GET"])
        )
        self.app.router.routes.append(Route(self.docs_url, docs_view, methods=["GET"]))
        self.app.router.routes.append(
            Route(self.redoc_url, redoc_view, methods=["GET"])
        )
