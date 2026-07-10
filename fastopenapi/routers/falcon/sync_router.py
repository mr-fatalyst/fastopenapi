from collections.abc import Callable
from typing import Any

import falcon

from fastopenapi.core.router import RouteInfo
from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui
from fastopenapi.response.serializer import WireResponse
from fastopenapi.routers.base import BaseAdapter
from fastopenapi.routers.common import RequestEnvelope
from fastopenapi.routers.falcon.extractors import FalconRequestDataExtractor


class FalconRouter(BaseAdapter):
    """Falcon adapter for FastOpenAPI"""

    ASYNC_ENDPOINT_ERROR: str | None = (
        "cannot be used with sync router. Use FalconAsyncRouter for async support."
    )

    extractor_cls = FalconRequestDataExtractor

    # Method mapping
    METHODS_MAPPER = {
        "GET": "on_get",
        "POST": "on_post",
        "PUT": "on_put",
        "PATCH": "on_patch",
        "DELETE": "on_delete",
        "HEAD": "on_head",
        "OPTIONS": "on_options",
    }

    def __init__(self, app: "falcon.App[Any, Any] | None" = None, **kwargs: Any):
        self._resources: dict[str, Any] = {}
        super().__init__(app, **kwargs)

    def add_route(
        self,
        path: str,
        method: str,
        endpoint: Callable[..., Any],
        meta: dict[str, Any] | None = None,
    ) -> RouteInfo:
        """Add route to Falcon application"""
        route = super().add_route(path, method, endpoint, meta)

        if self.app is not None:
            resource = self._create_or_update_resource(
                path, method.upper(), endpoint, route.meta
            )
            self.app.add_route(path, resource)
        return route

    def _create_or_update_resource(
        self,
        path: str,
        method: str,
        endpoint: Callable[..., Any],
        meta: dict[str, Any],
    ) -> Any:
        """Create or update Falcon resource"""
        resource = self._get_or_create_resource(path)
        method_name = self.METHODS_MAPPER.get(method, f"on_{method.lower()}")
        handler = self._build_response_handler(endpoint, meta)
        setattr(resource, method_name, handler)
        if method == "GET":
            self._register_auto_head(resource, handler)
        return resource

    def _get_or_create_resource(self, path: str) -> Any:
        """Get existing resource or create new one"""
        if path not in self._resources:
            self._resources[path] = type("DynamicResource", (), {})()
        return self._resources[path]

    def _register_auto_head(
        self, resource: Any, get_handler: Callable[..., Any]
    ) -> None:
        """Answer HEAD on GET routes unless an explicit HEAD is registered.

        An explicit ``on_head`` (registered before or after the GET route)
        always wins over the auto-generated one.
        """
        existing = getattr(resource, "on_head", None)
        if existing is not None and not getattr(
            existing, "_fastopenapi_auto_head", False
        ):
            return
        head_handler = self._build_head_handler(get_handler)
        setattr(head_handler, "_fastopenapi_auto_head", True)
        resource.on_head = head_handler

    def _build_head_handler(
        self, get_handler: Callable[..., Any]
    ) -> Callable[..., None]:
        """Run the GET pipeline for HEAD, then drop the body"""

        def handle_head(request: Any, response: Any, **path_params: Any) -> None:
            get_handler(request, response, **path_params)
            response.media = None
            response.text = None
            response.data = None

        return handle_head

    def _build_response_handler(
        self, endpoint: Callable[..., Any], meta: dict[str, Any]
    ) -> Callable[..., None]:
        """Build request handler function for endpoint"""

        def handle(request: Any, response: Any, **path_params: Any) -> None:
            env = RequestEnvelope(request=request, path_params=path_params)
            result = self.handle_request(endpoint, env, meta)

            if isinstance(result, WireResponse):
                self._apply_wire_response(result, response)
            elif isinstance(result, falcon.Response):  # pragma: no cover
                self._copy_falcon_response(result, response)

        return handle

    @staticmethod
    def _apply_wire_response(wire: WireResponse, response: Any) -> None:
        """Apply the finalized triple to Falcon's response object"""
        response.status = wire.status
        for key, value in wire.headers.items():
            if key.lower() == "content-type":
                response.content_type = value
            else:
                response.set_header(key, value)
        if wire.body is not None:
            response.data = wire.body

    def _copy_falcon_response(self, source: falcon.Response, target: Any) -> None:
        """Copy a user-returned Falcon Response onto the live response"""
        target.status = source.status
        if source.media is not None:
            target.media = source.media
        elif source.text is not None:
            target.text = source.text
        elif source.data is not None:
            target.data = source.data
        if source.content_type:
            target.content_type = source.content_type
        for key, value in source.headers.items():
            target.set_header(key, value)

    def build_framework_response(self, response: WireResponse) -> WireResponse:
        """Falcon applies the triple to its response object in the handler"""
        return response

    def is_framework_response(self, response: Any) -> bool:
        return isinstance(response, falcon.Response)

    def _register_docs_endpoints(self) -> None:
        """Register documentation endpoints"""
        openapi_url = self.openapi_url
        if openapi_url is None:
            return
        # narrowing does not survive into nested class bodies
        schema_url: str = openapi_url
        outer = self

        class OpenAPISchemaResource:
            def on_get(self, req: Any, resp: Any) -> None:
                resp.media = outer.openapi

        class SwaggerUIResource:
            def on_get(self, req: Any, resp: Any) -> None:
                html = render_swagger_ui(schema_url)
                resp.content_type = "text/html"
                resp.text = html

        class RedocUIResource:
            def on_get(self, req: Any, resp: Any) -> None:
                html = render_redoc_ui(schema_url)
                resp.content_type = "text/html"
                resp.text = html

        self.app.add_route(openapi_url, OpenAPISchemaResource())
        if self.docs_url:
            self.app.add_route(self.docs_url, SwaggerUIResource())
        if self.redoc_url:
            self.app.add_route(self.redoc_url, RedocUIResource())
