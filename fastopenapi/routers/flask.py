from collections.abc import Callable

from flask import Response as FlaskResponse
from flask import jsonify, request

from fastopenapi.core.types import Response
from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui
from fastopenapi.routers.base import BaseAdapter


class FlaskRouter(BaseAdapter):
    """Flask adapter for FastOpenAPI"""

    def add_route(self, path: str, method: str, endpoint: Callable):
        """Add route to Flask application"""
        super().add_route(path, method, endpoint)

        if self.app is not None:
            flask_path = self._convert_path_for_framework(path, "flask")

            def view_func(**path_params):
                synthetic_request = type(
                    "Request",
                    (),
                    {
                        "path_params": path_params,
                        "args": request.args,
                        "json": request.get_json(silent=True),
                        "headers": request.headers,
                        "cookies": request.cookies,
                        "form": request.form,
                        "files": request.files,
                    },
                )()

                if self.is_async_endpoint(endpoint):
                    error_response = {
                        "error": {
                            "type": "unsupported_endpoint",
                            "message": f"Async endpoint '{endpoint.__name__}' "
                            f"cannot be used with Flask. Use Quart for async support.",
                            "status": 500,
                        }
                    }
                    return jsonify(error_response), 500

                return self.handle_request_sync(endpoint, synthetic_request)

            self.app.add_url_rule(
                flask_path, endpoint.__name__, view_func, methods=[method.upper()]
            )

    def _get_path_params(self, request) -> dict:
        return getattr(request, "path_params", {})

    def _get_query_params(self, request) -> dict:
        query_params = {}
        for key in request.args:
            values = request.args.getlist(key)
            query_params[key] = values[0] if len(values) == 1 else values
        return query_params

    def _get_headers(self, request) -> dict:
        return dict(request.headers)

    def _get_cookies(self, request) -> dict:
        return dict(request.cookies)

    def _get_body_sync(self, request) -> dict:
        return request.json or {}

    async def _get_body_async(self, request) -> dict:
        # Flask doesn't support async
        return self._get_body_sync(request)

    def _get_form_data_sync(self, request) -> dict:
        return dict(request.form) if hasattr(request, "form") else {}

    async def _get_form_and_files_async(self, request) -> tuple[dict, dict]:
        # Flask doesn't support async
        return self._get_form_data_sync(request), self._get_files_sync(request)

    def _get_files_sync(self, request) -> dict:
        files = {}
        if hasattr(request, "files"):
            for name, file in request.files.items():
                # Read file content into temporary file
                content = file.stream.read()
                files[name] = self._save_upload_file_sync(content, file.filename)
        return files

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
