import inspect
import re
from collections.abc import Callable

from django.core.exceptions import BadRequest, PermissionDenied
from django.http import Http404, HttpResponse, HttpResponseBase, JsonResponse
from django.urls import path as django_path
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from pydantic_core import to_json

from fastopenapi.core.types import Response
from fastopenapi.errors.exceptions import (
    AuthorizationError,
    BadRequestError,
    ResourceNotFoundError,
)
from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui
from fastopenapi.routers.base import BaseAdapter
from fastopenapi.routers.common import RequestEnvelope
from fastopenapi.routers.django.extractors import DjangoRequestDataExtractor


class DjangoRouter(BaseAdapter):
    """Django adapter for FastOpenAPI"""

    PATH_CONVERSIONS = (r"{(\w+)}", r"<\1>")

    EXCEPTION_MAPPER = {
        Http404: ResourceNotFoundError,
        PermissionDenied: AuthorizationError,
        BadRequest: BadRequestError,
    }

    extractor_cls = DjangoRequestDataExtractor

    def __init__(self, app=None, **kwargs):
        self._views = {}
        super().__init__(app, **kwargs)

    def add_route(self, path: str, method: str, endpoint: Callable):
        """Add route to Django URL patterns"""
        super().add_route(path, method, endpoint)
        self._create_or_update_view(path, method, endpoint)

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

        def handle(self, req, **path_params):  # pragma: no cover
            env = RequestEnvelope(request=req, path_params=path_params)
            if inspect.iscoroutinefunction(endpoint):
                raise Exception(
                    f"Async endpoint '{endpoint.__name__}' "
                    f"cannot be used with sync router. "
                    f"Use DjangoAsyncRouter for async support."
                )
            return outer.handle_request(endpoint, env)

        setattr(view, method_name, handle)
        return view

    def build_framework_response(self, response: Response) -> HttpResponse:
        """Build Django response"""
        if response.content is None:
            http_response = HttpResponse(status=response.status_code)
        else:
            http_response = HttpResponse(
                content=to_json(response.content).decode("utf-8"),
                status=response.status_code,
                content_type="application/json",
            )

        for key, value in response.headers.items():
            http_response[key] = value

        return http_response

    def is_framework_response(self, response: Response | HttpResponseBase) -> bool:
        return isinstance(response, HttpResponseBase)

    def _register_docs_endpoints(self):  # pragma: no cover
        """Register documentation endpoints"""
        outer = self

        class OpenAPISchemaView(View):
            @csrf_exempt
            def get(self, req):
                return JsonResponse(outer.openapi)

        class SwaggerUIView(View):
            def get(self, req):
                return HttpResponse(
                    render_swagger_ui(outer.openapi_url).encode(),
                    content_type="text/html",
                )

        class RedocUIView(View):
            def get(self, req):
                return HttpResponse(
                    render_redoc_ui(outer.openapi_url).encode(),
                    content_type="text/html",
                )

        self._views[self.openapi_url] = OpenAPISchemaView
        self._views[self.docs_url] = SwaggerUIView
        self._views[self.redoc_url] = RedocUIView

    @property
    def urls(self):
        """Get Django URL patterns"""
        return (
            tuple(
                django_path(
                    re.sub(r"{(\w+)}", r"<\1>", path).lstrip("/"),
                    view_class.as_view(),
                    name=view_class.__class__.__name__,
                )
                for path, view_class in self._views.items()
            ),
            "fastopenapi",
            f"api-{self.version}",
        )
