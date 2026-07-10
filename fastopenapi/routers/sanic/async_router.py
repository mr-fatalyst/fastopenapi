from collections.abc import Callable
from typing import Any

from sanic import response

from fastopenapi.core.router import RouteInfo
from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui
from fastopenapi.response.serializer import WireResponse
from fastopenapi.routers.base import BaseAdapter
from fastopenapi.routers.common import RequestEnvelope
from fastopenapi.routers.sanic.extractors import SanicRequestDataExtractor


class SanicRouter(BaseAdapter):
    """Sanic adapter for FastOpenAPI"""

    PATH_CONVERSIONS = (r"{(\w+)}", r"<\1>")
    extractor_async_cls = SanicRequestDataExtractor

    def __init__(self, app: Any = None, **kwargs: Any):
        self._explicit_head_paths: set[str] = set()
        self._auto_head_paths: set[str] = set()
        super().__init__(app, **kwargs)

    def add_route(
        self,
        path: str,
        method: str,
        endpoint: Callable[..., Any],
        meta: dict[str, Any] | None = None,
    ) -> RouteInfo:
        """Add route to Sanic application"""
        route = super().add_route(path, method, endpoint, meta)

        if self.app is None:
            return route

        method = method.upper()
        sanic_path = self._convert_path_for_framework(path)
        route_meta = route.meta

        async def view_func(request: Any, **path_params: Any) -> Any:
            env = RequestEnvelope(request=request, path_params=path_params)
            return await self.handle_request_async(endpoint, env, route_meta)

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
        return route

    def build_framework_response(self, response_obj: WireResponse) -> Any:
        """Wrap the finalized triple into a Sanic response"""
        headers = dict(response_obj.headers)
        content_type = None
        for key in [k for k in headers if k.lower() == "content-type"]:
            content_type = headers.pop(key)
        return response.HTTPResponse(
            body=response_obj.body if response_obj.body is not None else b"",
            status=response_obj.status,
            headers=headers,
            content_type=content_type,
        )

    def is_framework_response(self, resp: Any) -> bool:
        return isinstance(resp, response.BaseHTTPResponse)

    def _register_docs_endpoints(self) -> None:
        """Register documentation endpoints"""
        openapi_url = self.openapi_url
        if openapi_url is None:
            return

        async def openapi_view(request: Any) -> Any:
            return response.json(self.openapi)

        self.app.add_route(
            openapi_view, openapi_url, methods=["GET"], name="openapi_view"
        )

        if self.docs_url:

            async def docs_view(request: Any) -> Any:
                html = render_swagger_ui(openapi_url)
                return response.html(html)

            self.app.add_route(
                docs_view, self.docs_url, methods=["GET"], name="docs_view"
            )

        if self.redoc_url:

            async def redoc_view(request: Any) -> Any:
                html = render_redoc_ui(openapi_url)
                return response.html(html)

            self.app.add_route(
                redoc_view, self.redoc_url, methods=["GET"], name="redoc_view"
            )
