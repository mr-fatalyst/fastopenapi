from collections.abc import Callable

from sanic import response

from fastopenapi.core.types import Response
from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui
from fastopenapi.routers.base import BaseAdapter
from fastopenapi.routers.common import RequestEnvelope
from fastopenapi.routers.sanic.extractors import SanicRequestDataExtractor


class SanicRouter(BaseAdapter):
    """Sanic adapter for FastOpenAPI"""

    PATH_CONVERSIONS = (r"{(\w+)}", r"<\1>")
    extractor_async_cls = SanicRequestDataExtractor

    def add_route(self, path: str, method: str, endpoint: Callable):
        """Add route to Sanic application"""
        super().add_route(path, method, endpoint)

        if self.app is None:
            return

        sanic_path = self._convert_path_for_framework(path)

        async def view_func(request, **path_params):
            env = RequestEnvelope(request=request, path_params=path_params)
            return await self.handle_request_async(endpoint, env)

        route_name = f"{endpoint.__name__}_{method.lower()}_{path.replace('/', '_')}"
        self.app.add_route(
            view_func, sanic_path, methods=[method.upper()], name=route_name
        )

    def build_framework_response(self, response_obj: Response):
        """Build Sanic response"""
        return response.json(
            response_obj.content,
            status=response_obj.status_code,
            headers=response_obj.headers,
        )

    def _register_docs_endpoints(self):
        """Register documentation endpoints"""

        @self.app.route(self.openapi_url, methods=["GET"])
        async def openapi_view(request):
            return response.json(self.openapi)

        @self.app.route(self.docs_url, methods=["GET"])
        async def docs_view(request):
            html = render_swagger_ui(self.openapi_url)
            return response.html(html)

        @self.app.route(self.redoc_url, methods=["GET"])
        async def redoc_view(request):
            html = render_redoc_ui(self.openapi_url)
            return response.html(html)
