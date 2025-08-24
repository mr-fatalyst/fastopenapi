import inspect
from collections.abc import Callable
from http import HTTPStatus

import falcon

from fastopenapi.core.types import Response
from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui
from fastopenapi.routers.base import (
    BaseAdapter,
    RequestEnvelope,
)
from fastopenapi.routers.falcon.constants import HTTP_STATUS_TO_FALCON, METHODS_MAPPER
from fastopenapi.routers.falcon.extractors import FalconRequestDataExtractor


class FalconRouter(BaseAdapter):
    """Falcon adapter for FastOpenAPI"""

    extractor_cls = FalconRequestDataExtractor

    def __init__(self, app: falcon.App = None, **kwargs):
        self._resources = {}
        super().__init__(app, **kwargs)

    def add_route(self, path: str, method: str, endpoint: Callable):
        """Add route to Falcon application"""
        super().add_route(path, method, endpoint)

        if self.app is not None:
            resource = self._create_or_update_resource(path, method.upper(), endpoint)
            self.app.add_route(path, resource)

    def _get_falcon_status(self, status_code: int) -> str:
        """Get Falcon status constant"""
        http_status = HTTPStatus(status_code)
        return HTTP_STATUS_TO_FALCON.get(http_status, falcon.HTTP_500)

    def _create_or_update_resource(self, path: str, method: str, endpoint):
        """Create or update Falcon resource"""
        resource = self._resources.get(path)
        if not resource:
            resource = type("DynamicResource", (), {})()
            self._resources[path] = resource

        method_name = METHODS_MAPPER.get(method, f"on_{method.lower()}")

        def handle(request, response, **path_params):
            env = RequestEnvelope(request=request, path_params=path_params)

            if inspect.iscoroutinefunction(endpoint):
                raise Exception(
                    f"Async endpoint '{endpoint.__name__}' "
                    f"cannot be used with sync router. "
                    f"Use FalconAsyncRouter for async support."
                )
            else:
                result_response = self.handle_request(endpoint, env)

            # Falcon needs special handling
            if isinstance(result_response, Response):
                response.status = self._get_falcon_status(result_response.status_code)
                response.media = result_response.content
                for key, value in result_response.headers.items():
                    response.set_header(key, value)

        setattr(resource, method_name, handle)
        return resource

    def build_framework_response(self, response: Response) -> Response:
        """Build Falcon response"""
        return response

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
