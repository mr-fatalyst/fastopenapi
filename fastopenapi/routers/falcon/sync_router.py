import inspect
from collections.abc import Callable

import falcon

from fastopenapi.core.types import Response
from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui
from fastopenapi.routers.base import BaseAdapter
from fastopenapi.routers.common import RequestEnvelope
from fastopenapi.routers.falcon.extractors import FalconRequestDataExtractor


class FalconRouter(BaseAdapter):
    """Falcon adapter for FastOpenAPI"""

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

    def __init__(self, app: falcon.App = None, **kwargs):
        self._resources = {}
        super().__init__(app, **kwargs)

    def add_route(self, path: str, method: str, endpoint: Callable):
        """Add route to Falcon application"""
        super().add_route(path, method, endpoint)

        if self.app is not None:
            resource = self._create_or_update_resource(path, method.upper(), endpoint)
            self.app.add_route(path, resource)

    def _create_or_update_resource(self, path: str, method: str, endpoint):
        """Create or update Falcon resource"""
        resource = self._get_or_create_resource(path)
        method_name = self.METHODS_MAPPER.get(method, f"on_{method.lower()}")
        handler = self._build_response_handler(endpoint)
        setattr(resource, method_name, handler)
        return resource

    def _get_or_create_resource(self, path: str):
        """Get existing resource or create new one"""
        if path not in self._resources:
            self._resources[path] = type("DynamicResource", (), {})()
        return self._resources[path]

    def _build_response_handler(self, endpoint: Callable):
        """Build request handler function for endpoint"""

        def handle(request, response, **path_params):
            if inspect.iscoroutinefunction(endpoint):
                raise Exception(
                    f"Async endpoint '{endpoint.__name__}' "
                    f"cannot be used with sync router. "
                    f"Use FalconAsyncRouter for async support."
                )

            env = RequestEnvelope(request=request, path_params=path_params)
            result_response = self.handle_request(endpoint, env)

            if isinstance(result_response, Response):
                self._apply_falcon_response(result_response, response)
            elif isinstance(result_response, falcon.Response):  # pragma: no cover
                self._copy_falcon_response(result_response, response)

        return handle

    def _apply_falcon_response(self, result_response: Response, response):
        """Apply our Response to Falcon response object"""
        response.status = result_response.status_code

        # For 204 No Content, no body or content-type should be set
        if result_response.status_code == 204:
            return

        content_type = result_response.headers.get("Content-Type")

        # Binary content
        if isinstance(result_response.content, bytes):
            response.data = result_response.content
            response.content_type = content_type or "application/octet-stream"
        # String non-JSON content
        elif isinstance(result_response.content, str) and content_type not in [
            "application/json",
            "text/json",
        ]:
            response.text = result_response.content
            response.content_type = content_type or "text/plain"
        # JSON content
        else:
            response.media = result_response.content
            response.content_type = content_type or "application/json"

        # Set custom headers (except Content-Type, already set)
        for key, value in result_response.headers.items():
            if key.lower() != "content-type":
                response.set_header(key, value)

    def _copy_falcon_response(self, source: falcon.Response, target):
        """Copy Falcon Response to response object"""
        target.status = source.status_code
        target.media = source.media
        for key, value in source.headers.items():
            target.set_header(key, value)

    def build_framework_response(self, response: Response) -> Response:
        """Build Falcon response"""
        return response

    def is_framework_response(self, response: Response | falcon.Response) -> bool:
        return isinstance(response, falcon.Response)

    def _register_docs_endpoints(self):
        """Register documentation endpoints"""
        outer = self

        class OpenAPISchemaResource:
            def on_get(self, req, resp):
                resp.media = outer.openapi

        class SwaggerUIResource:
            def on_get(self, req, resp):
                html = render_swagger_ui(outer.openapi_url)
                resp.content_type = "text/html"
                resp.text = html

        class RedocUIResource:
            def on_get(self, req, resp):
                html = render_redoc_ui(outer.openapi_url)
                resp.content_type = "text/html"
                resp.text = html

        self.app.add_route(self.openapi_url, OpenAPISchemaResource())
        self.app.add_route(self.docs_url, SwaggerUIResource())
        self.app.add_route(self.redoc_url, RedocUIResource())
