from collections.abc import Callable
from typing import Any

from django.core.exceptions import BadRequest, PermissionDenied
from django.http import Http404, HttpResponse, HttpResponseBase, JsonResponse
from django.urls import path as django_path
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from fastopenapi.core.router import RouteInfo
from fastopenapi.errors.exceptions import (
    AuthorizationError,
    BadRequestError,
    ResourceNotFoundError,
)
from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui
from fastopenapi.response.serializer import WireResponse
from fastopenapi.routers.base import BaseAdapter
from fastopenapi.routers.common import RequestEnvelope
from fastopenapi.routers.django.extractors import DjangoRequestDataExtractor


class DjangoRouter(BaseAdapter):
    """Django adapter for FastOpenAPI"""

    PATH_CONVERSIONS = (r"{(\w+)}", r"<\1>")
    ASYNC_ENDPOINT_ERROR: str | None = (
        "cannot be used with sync router. Use DjangoAsyncRouter for async support."
    )

    EXCEPTION_MAPPER = {
        Http404: ResourceNotFoundError,
        PermissionDenied: AuthorizationError,
        BadRequest: BadRequestError,
    }

    extractor_cls = DjangoRequestDataExtractor

    def __init__(
        self,
        app: Any = None,
        register_docs: bool | None = None,
        **kwargs: Any,
    ) -> None:
        """Django has no application object; pass register_docs=True to
        serve the docs endpoints (legacy app=True keeps working)."""
        self._views: dict[str, Any] = {}
        if register_docs is not None:
            app = True if register_docs else None
        super().__init__(app, **kwargs)

    def add_route(
        self,
        path: str,
        method: str,
        endpoint: Callable[..., Any],
        meta: dict[str, Any] | None = None,
    ) -> RouteInfo:
        """Add route to Django URL patterns"""
        route = super().add_route(path, method, endpoint, meta)
        self._create_or_update_view(path, method, endpoint, route.meta)
        return route

    # Flipped by DjangoAsyncRouter: Django's view_is_async ignores the
    # options handler, so an async view whose only method is OPTIONS would
    # otherwise be dispatched synchronously
    VIEW_IS_ASYNC = False

    def _create_or_update_view(
        self,
        path: str,
        method: str,
        endpoint: Callable[..., Any],
        meta: dict[str, Any],
    ) -> Any:
        """Create or update Django view for the path"""
        view = self._views.get(path)
        if not view:
            attrs: dict[str, Any] = {"dispatch": csrf_exempt(View.dispatch)}
            if self.VIEW_IS_ASYNC:
                attrs["view_is_async"] = True
            view = type("DynamicView", (View,), attrs)
            self._views[path] = view

        setattr(view, method.lower(), self._build_view_handler(endpoint, meta))
        return view

    def _build_view_handler(
        self, endpoint: Callable[..., Any], meta: dict[str, Any]
    ) -> Callable[..., Any]:
        """Build the per-endpoint view method (async router overrides)"""
        outer = self

        def handle(self: Any, req: Any, **path_params: Any) -> Any:  # pragma: no cover
            env = RequestEnvelope(request=req, path_params=path_params)
            return outer.handle_request(endpoint, env, meta)

        return handle

    def build_framework_response(self, response: WireResponse) -> HttpResponse:
        """Wrap the finalized triple into a Django response"""
        http_response = HttpResponse(
            content=response.body if response.body is not None else b"",
            status=response.status,
            content_type=response.headers.get("Content-Type"),
        )
        # Django pre-sets a default text/html Content-Type; the wire
        # headers are the single source of truth
        if "Content-Type" not in response.headers:
            del http_response["Content-Type"]
        for key, value in response.headers.items():
            if key.lower() != "content-type":
                http_response[key] = value
        return http_response

    def is_framework_response(self, response: Any) -> bool:
        return isinstance(response, HttpResponseBase)

    def _register_docs_endpoints(self) -> None:  # pragma: no cover
        """Register documentation endpoints"""
        openapi_url = self.openapi_url
        if openapi_url is None:
            return
        # narrowing does not survive into nested class bodies
        schema_url: str = openapi_url
        outer = self

        class OpenAPISchemaView(View):
            # GET is CSRF-safe, no exemption needed
            def get(self, req: Any) -> HttpResponse:
                return JsonResponse(outer.openapi)

        class SwaggerUIView(View):
            def get(self, req: Any) -> HttpResponse:
                return HttpResponse(
                    render_swagger_ui(schema_url).encode(),
                    content_type="text/html",
                )

        class RedocUIView(View):
            def get(self, req: Any) -> HttpResponse:
                return HttpResponse(
                    render_redoc_ui(schema_url).encode(),
                    content_type="text/html",
                )

        self._views[openapi_url] = OpenAPISchemaView
        if self.docs_url:
            self._views[self.docs_url] = SwaggerUIView
        if self.redoc_url:
            self._views[self.redoc_url] = RedocUIView

    @property
    def urls(self) -> tuple[Any, str, str]:
        """Get Django URL patterns"""
        return (
            tuple(
                django_path(
                    self._convert_path_for_framework(path).lstrip("/"),
                    view_class.as_view(),
                    name=path.strip("/")
                    .replace("/", "_")
                    .replace("{", "")
                    .replace("}", "")
                    or "root",
                )
                for path, view_class in self._views.items()
            ),
            "fastopenapi",
            f"api-{self.version}",
        )
