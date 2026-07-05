from collections.abc import Callable
from typing import Any

from flask import Response as FlaskResponse
from flask import jsonify, request

from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui
from fastopenapi.response.serializer import WireResponse
from fastopenapi.routers.base import BaseAdapter
from fastopenapi.routers.common import RequestEnvelope
from fastopenapi.routers.flask.extractors import FlaskRequestDataExtractor


class FlaskRouter(BaseAdapter):
    """Flask adapter for FastOpenAPI"""

    PATH_CONVERSIONS = (r"{(\w+)}", r"<\1>")
    ASYNC_ENDPOINT_ERROR = "cannot be used with Flask. Use Quart for async support."

    extractor_cls = FlaskRequestDataExtractor

    def add_route(self, path: str, method: str, endpoint: Callable[..., Any]) -> None:
        """Add route to Flask application"""
        super().add_route(path, method, endpoint)

        if self.app is not None:
            flask_path = self._convert_path_for_framework(path)

            def view_func(**path_params):
                env = RequestEnvelope(request=request, path_params=path_params)
                return self.handle_request(endpoint, env)

            rule_endpoint = f"{endpoint.__name__}:{method.upper()}:{flask_path}"
            self.app.add_url_rule(
                flask_path, rule_endpoint, view_func, methods=[method.upper()]
            )

    def build_framework_response(self, response: WireResponse) -> FlaskResponse:
        """Wrap the finalized triple into a Flask response"""
        flask_response = FlaskResponse(
            response=response.body if response.body is not None else b"",
            status=response.status,
        )
        # Werkzeug pre-sets a default text/html Content-Type; the wire
        # headers are the single source of truth
        if "Content-Type" not in response.headers:
            flask_response.headers.remove("Content-Type")
        for key, value in response.headers.items():
            flask_response.headers[key] = value
        return flask_response

    def is_framework_response(self, response: Any) -> bool:
        return isinstance(response, FlaskResponse)

    def _register_docs_endpoints(self) -> None:
        """Register documentation endpoints"""

        @self.app.route(self.openapi_url, methods=["GET"])
        def openapi_view():
            return jsonify(self.openapi)

        if self.docs_url:

            @self.app.route(self.docs_url, methods=["GET"])
            def docs_view():
                html = render_swagger_ui(self.openapi_url)
                return FlaskResponse(html, mimetype="text/html")

        if self.redoc_url:

            @self.app.route(self.redoc_url, methods=["GET"])
            def redoc_view():
                html = render_redoc_ui(self.openapi_url)
                return FlaskResponse(html, mimetype="text/html")
