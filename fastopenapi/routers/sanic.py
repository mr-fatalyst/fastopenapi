from collections.abc import Callable

from sanic import response

from fastopenapi.core.types import Response
from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui
from fastopenapi.routers.base import BaseAdapter


class SanicRouter(BaseAdapter):
    """Sanic adapter for FastOpenAPI"""

    def add_route(self, path: str, method: str, endpoint: Callable):
        """Add route to Sanic application"""
        super().add_route(path, method, endpoint)

        if self.app is None:
            return

        sanic_path = self._convert_path_for_framework(path, "sanic")

        async def view_func(request, **path_params):
            synthetic_request = type(
                "Request",
                (),
                {"path_params": path_params, "_request": request},
            )()

            if self.is_async_endpoint(endpoint):
                return await self.handle_request_async(endpoint, synthetic_request)
            else:
                return self.handle_request_sync(endpoint, synthetic_request)

        route_name = f"{endpoint.__name__}_{method.lower()}_{path.replace('/', '_')}"
        self.app.add_route(
            view_func, sanic_path, methods=[method.upper()], name=route_name
        )

    def _get_path_params(self, request) -> dict:
        return getattr(request, "path_params", {})

    def _get_query_params(self, request) -> dict:
        query_params = {}
        req = request._request
        for k, v in req.args.items():
            values = req.args.getlist(k)
            query_params[k] = values[0] if len(values) == 1 else values
        return query_params

    def _get_headers(self, request) -> dict:
        return dict(request._request.headers)

    def _get_cookies(self, request) -> dict:
        return dict(request._request.cookies)

    def _get_body_sync(self, request) -> dict:
        return request._request.json or {}

    async def _get_body_async(self, request) -> dict:
        return request._request.json or {}

    def _get_form_data_sync(self, request) -> dict:
        form_data = {}
        if hasattr(request._request, "form"):
            for key in request._request.form:
                form_data[key] = request._request.form.get(key)
        return form_data

    async def _get_form_async(self, request) -> tuple[dict, dict]:
        form_data = self._get_form_data_sync(request)
        return form_data

    def _get_files_sync(self, request) -> dict:
        files = {}
        # if hasattr(request._request, "files"):
        #     for name, file_list in request._request.files.items():
        #         if file_list:
        #             file = file_list[0]
        #             # Save to temporary file
        #             files[name] = self._save_upload_file_sync(
        #                 file.body, file.name  # Sanic stores file content as bytes
        #             )
        return files

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
