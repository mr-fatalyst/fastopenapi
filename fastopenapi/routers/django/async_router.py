from collections.abc import Callable
from typing import Any

from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui
from fastopenapi.routers.common import RequestEnvelope
from fastopenapi.routers.django.extractors import DjangoAsyncRequestDataExtractor
from fastopenapi.routers.django.sync_router import DjangoRouter


class DjangoAsyncRouter(DjangoRouter):
    # Async endpoints are the whole point here — lift the sync-router guard
    ASYNC_ENDPOINT_ERROR = None
    extractor_async_cls = DjangoAsyncRequestDataExtractor

    def _build_view_handler(self, endpoint: Callable[..., Any]) -> Callable[..., Any]:
        """Build the per-endpoint async view method"""
        outer = self

        async def handle(self, req, **path_params):
            env = RequestEnvelope(request=req, path_params=path_params)
            return await outer.handle_request_async(endpoint, env)

        return handle

    def _register_docs_endpoints(self) -> None:
        """Register documentation endpoints"""
        outer = self

        class OpenAPISchemaView(View):
            @csrf_exempt
            async def get(self, req):
                return JsonResponse(outer.openapi)

        class SwaggerUIView(View):
            async def get(self, req):
                return HttpResponse(
                    render_swagger_ui(outer.openapi_url).encode(),
                    content_type="text/html",
                )

        class RedocUIView(View):
            async def get(self, req):
                return HttpResponse(
                    render_redoc_ui(outer.openapi_url).encode(),
                    content_type="text/html",
                )

        self._views[self.openapi_url] = OpenAPISchemaView
        if self.docs_url:
            self._views[self.docs_url] = SwaggerUIView
        if self.redoc_url:
            self._views[self.redoc_url] = RedocUIView
