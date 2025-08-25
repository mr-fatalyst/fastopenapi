from collections.abc import Callable

from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui
from fastopenapi.routers.common import RequestEnvelope
from fastopenapi.routers.django.extractors import DjangoAsyncRequestDataExtractor
from fastopenapi.routers.django.sync_router import DjangoRouter


class DjangoAsyncRouter(DjangoRouter):
    extractor_async_cls = DjangoAsyncRequestDataExtractor

    def _create_or_update_view(self, path: str, method: str, endpoint: Callable):
        """Create or update Django view for the path"""
        view = self._views.get(path)
        if not view:
            view = type(
                "DynamicView", (View,), {"dispatch": csrf_exempt(View.dispatch)}
            )
            self._views[path] = view

        method_name = method.lower()
        outer = self

        async def handle(self, req, **path_params):
            env = RequestEnvelope(request=req, path_params=path_params)
            return await outer.handle_request_async(endpoint, env)

        setattr(view, method_name, handle)
        return view

    def _register_docs_endpoints(self):
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
        self._views[self.docs_url] = SwaggerUIView
        self._views[self.redoc_url] = RedocUIView
