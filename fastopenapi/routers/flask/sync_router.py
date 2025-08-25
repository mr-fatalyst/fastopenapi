import inspect
from collections.abc import Callable

from flask import Response as FlaskResponse
from flask import jsonify, request

from fastopenapi.core.types import Response
from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui
from fastopenapi.routers.base import BaseAdapter
from fastopenapi.routers.common import RequestEnvelope
from fastopenapi.routers.flask.extractors import FlaskRequestDataExtractor


class FlaskRouter(BaseAdapter):
    """Flask adapter for FastOpenAPI"""

    PATH_CONVERSIONS = (r"{(\w+)}", r"<\1>")

    extractor_cls = FlaskRequestDataExtractor

    def add_route(self, path: str, method: str, endpoint: Callable):
        """Add route to Flask application"""
        super().add_route(path, method, endpoint)

        if self.app is not None:
            flask_path = self._convert_path_for_framework(path)

            def view_func(**path_params):
                env = RequestEnvelope(request=request, path_params=path_params)

                if inspect.iscoroutinefunction(endpoint):
                    raise Exception(
                        f"Async endpoint '{endpoint.__name__}' "
                        f"cannot be used with Flask. Use Quart for async support."
                    )

                return self.handle_request(endpoint, env)

            rule_endpoint = f"{endpoint.__name__}:{method.upper()}:{flask_path}"
            self.app.add_url_rule(
                flask_path, rule_endpoint, view_func, methods=[method.upper()]
            )

    def build_framework_response(self, response: Response) -> FlaskResponse:
        """Build Flask response"""
        flask_response = jsonify(response.content)
        flask_response.status_code = response.status_code

        for key, value in response.headers.items():
            flask_response.headers[key] = value

        return flask_response

    def _register_docs_endpoints(self):
        """Register documentation endpoints"""

        @self.app.route(self.openapi_url, methods=["GET"])
        def openapi_view():
            return jsonify(self.openapi)

        @self.app.route(self.docs_url, methods=["GET"])
        def docs_view():
            html = render_swagger_ui(self.openapi_url)
            return FlaskResponse(html, mimetype="text/html")

        @self.app.route(self.redoc_url, methods=["GET"])
        def redoc_view():
            html = render_redoc_ui(self.openapi_url)
            return FlaskResponse(html, mimetype="text/html")
