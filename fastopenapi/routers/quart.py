import re
from collections.abc import Callable

from quart import Response as QuartResponse
from quart import jsonify, request

from fastopenapi.core.types import RequestData, Response, UploadFile
from fastopenapi.errors.handler import format_exception_response
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
                return await self.handle_quart_request(endpoint, synthetic_request)

            self.app.add_url_rule(
                quart_path, endpoint.__name__, view_func, methods=[method.upper()]
            )

    async def handle_quart_request(self, endpoint: Callable, synthetic_request):
        """Handle Quart request"""
        try:
            request_data = await self.extract_request_data_async(synthetic_request)
            kwargs = self.resolver.resolve(endpoint, request_data)

            # Quart endpoints are always async
            result = await endpoint(**kwargs)

            response = self.response_builder.build(result, endpoint.__route_meta__)
            return self.build_framework_response(response)

        except Exception as e:
            error_response = format_exception_response(e)
            return jsonify(error_response), getattr(e, "status_code", 500)

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

    def extract_request_data(self, request) -> RequestData:
        """Not used in async adapter"""
        raise NotImplementedError("Use extract_request_data_async")

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
