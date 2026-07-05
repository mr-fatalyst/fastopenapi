from collections.abc import Callable
from typing import Any

from quart import Response as QuartResponse
from quart import jsonify, request

from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui
from fastopenapi.response.serializer import WireResponse
from fastopenapi.routers.base import BaseAdapter
from fastopenapi.routers.common import RequestEnvelope
from fastopenapi.routers.quart.extractors import QuartRequestDataExtractor


class QuartRouter(BaseAdapter):
    """Quart adapter for FastOpenAPI"""

    PATH_CONVERSIONS = (r"{(\w+)}", r"<\1>")

    extractor_async_cls = QuartRequestDataExtractor

    def add_route(self, path: str, method: str, endpoint: Callable[..., Any]) -> None:
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

    def build_framework_response(self, response: WireResponse) -> QuartResponse:
        """Wrap the finalized triple into a Quart response"""
        quart_response = QuartResponse(
            response.body if response.body is not None else b"",
            status=response.status,
        )
        # Quart pre-sets a default text/html Content-Type; the wire
        # headers are the single source of truth
        if (
            "Content-Type" not in response.headers
            and "Content-Type" in quart_response.headers
        ):
            del quart_response.headers["Content-Type"]
        for key, value in response.headers.items():
            quart_response.headers[key] = value
        return quart_response

    def is_framework_response(self, response: Any) -> bool:
        return isinstance(response, QuartResponse)

    def _register_docs_endpoints(self) -> None:
        """Register documentation endpoints"""

        @self.app.route(self.openapi_url, methods=["GET"])
        async def openapi_view():
            return jsonify(self.openapi)

        if self.docs_url:

            @self.app.route(self.docs_url, methods=["GET"])
            async def docs_view():
                html = render_swagger_ui(self.openapi_url)
                return QuartResponse(html, mimetype="text/html")

        if self.redoc_url:

            @self.app.route(self.redoc_url, methods=["GET"])
            async def redoc_view():
                html = render_redoc_ui(self.openapi_url)
                return QuartResponse(html, mimetype="text/html")
