import inspect
import re
from collections.abc import Callable

from quart import Response as QuartResponse
from quart import jsonify, request

from fastopenapi.core.types import RequestData, Response, UploadFile
from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui
from fastopenapi.routers.base import BaseAdapter


class QuartRouter(BaseAdapter):
    """Quart adapter for FastOpenAPI"""

    def add_route(self, path: str, method: str, endpoint: Callable):
        """Add route to Quart application"""
        super().add_route(path, method, endpoint)

        if self.app is not None:
            quart_path = re.sub(r"{(\w+)}", r"<\1>", path)

            async def view_func(**path_params):
                synthetic_request = type(
                    "Request",
                    (),
                    {
                        "path_params": path_params,
                    },
                )()

                # Check if endpoint is async and use appropriate handler
                if inspect.iscoroutinefunction(endpoint):
                    return await self.handle_request_async(endpoint, synthetic_request)
                else:
                    return self.handle_request_sync(endpoint, synthetic_request)

            self.app.add_url_rule(
                quart_path, endpoint.__name__, view_func, methods=[method.upper()]
            )

    async def extract_request_data_async(self, synthetic_request) -> RequestData:
        """Extract data from Quart request (async)"""
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
        body = await request.get_json(silent=True) or {}

        # Form data
        form_data = {}
        form = await request.form
        for key in form:
            form_data[key] = form[key]

        # Files
        files = {}
        files_data = await request.files
        for name, file in files_data.items():
            files[name] = UploadFile(
                filename=file.filename, content_type=file.content_type, file=file.stream
            )

        return RequestData(
            path_params=getattr(synthetic_request, "path_params", {}),
            query_params=query_params,
            headers=headers,
            cookies=cookies,
            body=body,
            form_data=form_data,
            files=files,
        )

    def extract_request_data(self, synthetic_request) -> RequestData:
        """Sync extraction for sync endpoints - simplified version"""
        # Query parameters
        query_params = {}
        for key in request.args:
            values = request.args.getlist(key)
            query_params[key] = values[0] if len(values) == 1 else values

        # Headers (normalize to lowercase)
        headers = {k.lower(): v for k, v in request.headers.items()}

        # Cookies
        cookies = dict(request.cookies)

        return RequestData(
            path_params=getattr(synthetic_request, "path_params", {}),
            query_params=query_params,
            headers=headers,
            cookies=cookies,
            body={},  # Body requires async reading
            form_data={},
            files={},
        )

    def build_framework_response(self, response: Response):
        """Build Quart response"""
        quart_response = jsonify(response.content)
        # Return tuple format for Quart
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
