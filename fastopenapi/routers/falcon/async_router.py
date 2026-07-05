from collections.abc import Callable
from typing import Any

from falcon import Response as FalconResponse

from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui
from fastopenapi.response.serializer import WireResponse
from fastopenapi.routers.common import RequestEnvelope
from fastopenapi.routers.falcon.extractors import FalconAsyncRequestDataExtractor
from fastopenapi.routers.falcon.sync_router import FalconRouter


class FalconAsyncRouter(FalconRouter):
    # Async endpoints are the whole point here — lift the sync-router guard
    ASYNC_ENDPOINT_ERROR = None
    extractor_async_cls = FalconAsyncRequestDataExtractor

    def _build_response_handler(
        self, endpoint: Callable[..., Any]
    ) -> Callable[..., Any]:
        """Build async request handler function for endpoint"""

        async def handle(request, response, **path_params):
            env = RequestEnvelope(request=request, path_params=path_params)
            result = await self.handle_request_async(endpoint, env)

            if isinstance(result, WireResponse):
                self._apply_wire_response(result, response)
            elif isinstance(result, FalconResponse):  # pragma: no cover
                self._copy_falcon_response(result, response)

        return handle

    def _build_head_handler(self, get_handler: Callable) -> Callable[..., Any]:
        """Run the GET pipeline for HEAD, then drop the body (async)"""

        async def handle_head(request, response, **path_params):
            await get_handler(request, response, **path_params)
            response.media = None
            response.text = None
            response.data = None

        return handle_head

    def _register_docs_endpoints(self) -> None:
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
        if self.docs_url:
            self.app.add_route(self.docs_url, SwaggerUIResource())
        if self.redoc_url:
            self.app.add_route(self.redoc_url, RedocUIResource())
