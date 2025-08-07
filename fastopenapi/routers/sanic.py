import inspect
import re
from collections.abc import Callable

from sanic import response

from fastopenapi.core.types import RequestData, Response, UploadFile
from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui
from fastopenapi.routers.base import BaseAdapter


class SanicRouter(BaseAdapter):
    """Sanic adapter for FastOpenAPI"""

    def add_route(self, path: str, method: str, endpoint: Callable):
        """Add route to Sanic application"""
        super().add_route(path, method, endpoint)

        if self.app is None:
            return

        sanic_path = re.sub(r"{(\w+)}", r"<\1>", path)

        async def view_func(request, **path_params):
            synthetic_request = type(
                "Request",
                (),
                {
                    "path_params": path_params,
                    "args": request.args,
                    "json": request.json,
                    "headers": request.headers,
                    "cookies": request.cookies,
                    "form": request.form,
                    "files": request.files,
                },
            )()

            # Check if endpoint is async and use appropriate handler
            if inspect.iscoroutinefunction(endpoint):
                return await self.handle_request_async(endpoint, synthetic_request)
            else:
                return self.handle_request_sync(endpoint, synthetic_request)

        route_name = f"{endpoint.__name__}_{method.lower()}_{path.replace('/', '_')}"
        self.app.add_route(
            view_func, sanic_path, methods=[method.upper()], name=route_name
        )

    def extract_request_data(self, request) -> RequestData:
        """Extract data from Sanic request"""
        # Query parameters
        query_params = {}
        for k, v in request.args.items():
            values = request.args.getlist(k)
            query_params[k] = values[0] if len(values) == 1 else values

        # Headers (normalize to lowercase)
        headers = {k.lower(): v for k, v in request.headers.items()}

        # Cookies
        cookies = dict(request.cookies)

        # Body
        body = request.json or {}

        # Form data
        form_data = {}
        if hasattr(request, "form"):
            for key in request.form:
                form_data[key] = request.form.get(key)

        # Files
        files = {}
        if hasattr(request, "files"):
            for name, file_list in request.files.items():
                if file_list:
                    file = file_list[0]  # Take first file if multiple
                    files[name] = UploadFile(
                        filename=file.name,
                        content_type=file.type,
                        file=file.body,  # Sanic stores file content as bytes
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
