from collections.abc import Callable
from typing import Any

from django.http import HttpResponse, JsonResponse
from django.views import View

from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui
from fastopenapi.routers.common import RequestEnvelope
from fastopenapi.routers.django.extractors import DjangoAsyncRequestDataExtractor
from fastopenapi.routers.django.sync_router import DjangoRouter


class DjangoAsyncRouter(DjangoRouter):
    # Async endpoints are the whole point here — lift the sync-router guard
    ASYNC_ENDPOINT_ERROR = None
    VIEW_IS_ASYNC = True
    extractor_async_cls = DjangoAsyncRequestDataExtractor

    def _build_view_handler(
        self, endpoint: Callable[..., Any], meta: dict[str, Any]
    ) -> Callable[..., Any]:
        """Build the per-endpoint async view method"""
        outer = self

        async def handle(self: Any, req: Any, **path_params: Any) -> Any:
            env = RequestEnvelope(request=req, path_params=path_params)
            return await outer.handle_request_async(endpoint, env, meta)

        return handle

    def _register_docs_endpoints(self) -> None:
        """Register documentation endpoints"""
        openapi_url = self.openapi_url
        if openapi_url is None:
            return
        # narrowing does not survive into nested class bodies
        schema_url: str = openapi_url
        outer = self

        class OpenAPISchemaView(View):
            # GET is CSRF-safe, no exemption needed
            async def get(self, req: Any) -> HttpResponse:
                return JsonResponse(outer.openapi)

        class SwaggerUIView(View):
            async def get(self, req: Any) -> HttpResponse:
                return HttpResponse(
                    render_swagger_ui(schema_url).encode(),
                    content_type="text/html",
                )

        class RedocUIView(View):
            async def get(self, req: Any) -> HttpResponse:
                return HttpResponse(
                    render_redoc_ui(schema_url).encode(),
                    content_type="text/html",
                )

        self._views[openapi_url] = OpenAPISchemaView
        if self.docs_url:
            self._views[self.docs_url] = SwaggerUIView
        if self.redoc_url:
            self._views[self.redoc_url] = RedocUIView
