from collections.abc import Callable

from quart import Response as QuartResponse
from quart import jsonify, request

from fastopenapi.core.types import Response
from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui
from fastopenapi.routers.base import BaseAdapter, RequestEnvelope
from fastopenapi.routers.quart.extractors import QuartRequestDataExtractor


class QuartRouter(BaseAdapter):
    """Quart adapter for FastOpenAPI"""

    PATH_CONVERSIONS = (r"{(\w+)}", r"<\1>")

    extractor_async_cls = QuartRequestDataExtractor

    def add_route(self, path: str, method: str, endpoint: Callable):
        """Add route to Quart application"""
        super().add_route(path, method, endpoint)

        if self.app is not None:
            quart_path = self._convert_path_for_framework(path)

            async def view_func(**path_params):
                env = RequestEnvelope(request=request, path_params=path_params)
                return await self.handle_request_async(endpoint, env)

            rule_endpoint = f"{endpoint.__name__}:{method.upper()}:{quart_path}"
            self.app.add_url_rule(
                quart_path, rule_endpoint, view_func, methods=[method.upper()]
            )

    def build_framework_response(self, response: Response):
        """Build Quart response"""
        quart_response = jsonify(response.content)
        return quart_response, response.status_code, response.headers

    def _register_docs_endpoints(self):
        """Register documentation endpoints"""

        @self.app.route(self.openapi_url, methods=["GET"])
        async def openapi_view():
            return jsonify(self.openapi)

        @self.app.route(self.docs_url, methods=["GET"])
        async def docs_view():
            html = render_swagger_ui(self.openapi_url)
            return QuartResponse(html, mimetype="text/html")

        @self.app.route(self.redoc_url, methods=["GET"])
        async def redoc_view():
            html = render_redoc_ui(self.openapi_url)
            return QuartResponse(html, mimetype="text/html")
