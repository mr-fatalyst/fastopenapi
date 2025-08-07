import inspect
import re
from collections.abc import Callable

from flask import Response as FlaskResponse
from flask import jsonify, request

from fastopenapi.core.types import RequestData, Response, UploadFile
from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui
from fastopenapi.routers.base import BaseAdapter


class FlaskRouter(BaseAdapter):
    """Flask adapter for FastOpenAPI"""

    def add_route(self, path: str, method: str, endpoint: Callable):
        """Add route to Flask application"""
        super().add_route(path, method, endpoint)

        if self.app is not None:
            flask_path = re.sub(r"{(\w+)}", r"<\1>", path)

            def view_func(**path_params):
                # Create synthetic request object with path params
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

                # Check if endpoint is async
                if inspect.iscoroutinefunction(endpoint):
                    error_response = {
                        "error": {
                            "type": "unsupported_endpoint",
                            "message": f"Async endpoint '{endpoint.__name__}' "
                            f"cannot be used with Flask. Use Quart for "
                            f"async support.",
                            "status": 500,
                        }
                    }
                    return jsonify(error_response), 500

                # Use sync handler
                return self.handle_request_sync(endpoint, synthetic_request)

            self.app.add_url_rule(
                flask_path, endpoint.__name__, view_func, methods=[method.upper()]
            )

    def extract_request_data(self, request) -> RequestData:
        """Extract data from Flask request"""
        # Query parameters
        query_params = {}
        for key in request.args:
            values = request.args.getlist(key)
            query_params[key] = values[0] if len(values) == 1 else values

        # Headers (normalize to lowercase)
        headers = {k.lower(): v for k, v in request.headers.items()}

        # Cookies
        cookies = dict(request.cookies)

        # Body
        body = request.json or {}

        # Form data
        form_data = dict(request.form) if hasattr(request, "form") else {}

        # Files
        files = {}
        if hasattr(request, "files"):
            for name, file in request.files.items():
                files[name] = UploadFile(
                    filename=file.filename,
                    content_type=file.content_type,
                    file=file.stream,
                )

        return RequestData(
            path_params=getattr(request, "path_params", {}),
            query_params=query_params,
            headers=headers,
            cookies=cookies,
            body=body,
            form_data=form_data,
            files=files,
        )

    def build_framework_response(self, response: Response) -> FlaskResponse:
        """Build Flask response"""
        flask_response = jsonify(response.content)
        flask_response.status_code = response.status_code

        # Add custom headers
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
