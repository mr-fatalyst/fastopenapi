from collections.abc import Callable

from quart import Response as QuartResponse
from quart import jsonify, request

from fastopenapi.core.types import Response, UploadFile
from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui
from fastopenapi.routers.base import BaseAdapter


class QuartRouter(BaseAdapter):
    """Quart adapter for FastOpenAPI"""

    def add_route(self, path: str, method: str, endpoint: Callable):
        """Add route to Quart application"""
        super().add_route(path, method, endpoint)

        if self.app is not None:
            quart_path = self._convert_path_for_framework(
                path, "flask"
            )  # Same as Flask

            async def view_func(**path_params):
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
                    return await self.handle_request_async(endpoint, synthetic_request)
                else:
                    return self.handle_request_sync(endpoint, synthetic_request)

            self.app.add_url_rule(
                quart_path, endpoint.__name__, view_func, methods=[method.upper()]
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
        # Sync endpoints in Quart have limited support
        return {}

    async def _get_body_async(self, request) -> dict:
        return await request.json or {}

    def _get_form_data_sync(self, request) -> dict:
        # Sync endpoints in Quart have limited support
        return {}

    async def _get_form_and_files_async(self, request) -> tuple[dict, dict]:
        form_data = {}
        files = {}

        form = await request.form
        for key in form:
            form_data[key] = form[key]

        files_data = await request.files
        for name, file in files_data.items():
            # Stream to temporary file
            import tempfile

            temp_file = tempfile.NamedTemporaryFile(delete=False)
            await file.save(temp_file.name)
            temp_file.seek(0)

            files[name] = UploadFile(
                filename=file.filename, content_type=file.content_type, file=temp_file
            )

        return form_data, files

    def _get_files_sync(self, request) -> dict:
        # Sync endpoints in Quart have limited support
        return {}

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
