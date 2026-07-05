from collections.abc import Callable
from typing import Any

from sanic import response

from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui
from fastopenapi.response.serializer import WireResponse
from fastopenapi.routers.base import BaseAdapter
from fastopenapi.routers.common import RequestEnvelope
from fastopenapi.routers.sanic.extractors import SanicRequestDataExtractor


class SanicRouter(BaseAdapter):
    """Sanic adapter for FastOpenAPI"""

    PATH_CONVERSIONS = (r"{(\w+)}", r"<\1>")
    extractor_async_cls = SanicRequestDataExtractor

    def __init__(self, app: Any = None, **kwargs):
        self._explicit_head_paths: set[str] = set()
        self._auto_head_paths: set[str] = set()
        super().__init__(app, **kwargs)

    def add_route(self, path: str, method: str, endpoint: Callable[..., Any]) -> None:
        """Add route to Sanic application"""
        super().add_route(path, method, endpoint)

        if self.app is None:
            return

        method = method.upper()
        sanic_path = self._convert_path_for_framework(path)

        async def view_func(request, **path_params):
            env = RequestEnvelope(request=request, path_params=path_params)
            return await self.handle_request_async(endpoint, env)

        methods = [method]
        if method == "HEAD":
            if path in self._auto_head_paths:
                raise TypeError(
                    f"Explicit HEAD route for '{path}' must be registered "
                    f"before its GET route (auto-HEAD is already in place)"
                )
            self._explicit_head_paths.add(path)
        elif method == "GET" and path not in self._explicit_head_paths:
            # Sanic itself omits the body for HEAD responses
            methods.append("HEAD")
            self._auto_head_paths.add(path)

        route_name = f"{endpoint.__name__}_{method.lower()}_{path.replace('/', '_')}"
        self.app.add_route(view_func, sanic_path, methods=methods, name=route_name)

    def build_framework_response(self, response_obj: WireResponse) -> Any:
        """Wrap the finalized triple into a Sanic response"""
        headers = dict(response_obj.headers)
        content_type = None
        for key in [k for k in headers if k.lower() == "content-type"]:
            content_type = headers.pop(key)
        return response.raw(
            response_obj.body if response_obj.body is not None else b"",
            status=response_obj.status,
            headers=headers,
            content_type=content_type,
        )

    def is_framework_response(self, resp: Any) -> bool:
        return isinstance(resp, response.BaseHTTPResponse)

    def _register_docs_endpoints(self) -> None:
        """Register documentation endpoints"""

        @self.app.route(self.openapi_url, methods=["GET"])
        async def openapi_view(request):
            return response.json(self.openapi)

        if self.docs_url:

            @self.app.route(self.docs_url, methods=["GET"])
            async def docs_view(request):
                html = render_swagger_ui(self.openapi_url)
                return response.html(html)

        if self.redoc_url:

            @self.app.route(self.redoc_url, methods=["GET"])
            async def redoc_view(request):
                html = render_redoc_ui(self.openapi_url)
                return response.html(html)
