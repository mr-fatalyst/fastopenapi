from falcon import Response as FalconResponse

from fastopenapi.core.types import Response
from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui
from fastopenapi.routers.common import RequestEnvelope
from fastopenapi.routers.falcon.extractors import FalconAsyncRequestDataExtractor
from fastopenapi.routers.falcon.sync_router import FalconRouter


class FalconAsyncRouter(FalconRouter):
    extractor_async_cls = FalconAsyncRequestDataExtractor

    def _create_or_update_resource(self, path: str, method: str, endpoint):
        """Create or update Falcon resource"""
        resource = self._resources.get(path)
        if not resource:
            resource = type("DynamicResource", (), {})()
            self._resources[path] = resource

        method_name = self.METHODS_MAPPER.get(method, f"on_{method.lower()}")

        async def handle(request, response, **path_params):
            env = RequestEnvelope(request=request, path_params=path_params)

            result_response = await self.handle_request_async(endpoint, env)

            # Falcon needs special handling
            if isinstance(result_response, Response):
                response.status = result_response.status_code
                response.media = result_response.content
                for key, value in result_response.headers.items():
                    response.set_header(key, value)
            elif isinstance(result_response, FalconResponse):  # pragma: no cover
                response.status = result_response.status_code
                response.media = result_response.media
                for key, value in result_response.headers.items():
                    response.set_header(key, value)

        setattr(resource, method_name, handle)
        return resource

    def _register_docs_endpoints(self):
        """Register documentation endpoints"""
        outer = self

        class OpenAPISchemaResource:
            async def on_get(self, req, resp):
                resp.media = outer.openapi

        class SwaggerUIResource:
            async def on_get(self, req, resp):
                html = render_swagger_ui(outer.openapi_url)
                resp.content_type = "text/html"
                resp.text = html

        class RedocUIResource:
            async def on_get(self, req, resp):
                html = render_redoc_ui(outer.openapi_url)
                resp.content_type = "text/html"
                resp.text = html

        self.app.add_route(self.openapi_url, OpenAPISchemaResource())
        self.app.add_route(self.docs_url, SwaggerUIResource())
        self.app.add_route(self.redoc_url, RedocUIResource())
