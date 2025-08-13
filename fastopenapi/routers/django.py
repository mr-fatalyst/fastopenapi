import re
from collections.abc import Callable
from http import HTTPStatus

from django.http import Http404, HttpResponse, JsonResponse
from django.urls import path as django_path
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from pydantic_core import from_json, to_json

from fastopenapi.core.types import Response, UploadFile
from fastopenapi.errors.exceptions import ResourceNotFoundError
from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui
from fastopenapi.routers.base import BaseAdapter


class DjangoRouter(BaseAdapter):
    """Django adapter for FastOpenAPI"""

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

        if self.is_async_endpoint(endpoint):

            async def handle(self, req, **path_params):
                synthetic_request = type(
                    "Request",
                    (),
                    {
                        "path_params": path_params,
                        "GET": req.GET,
                        "body": req.body,
                        "headers": req.headers,
                        "COOKIES": req.COOKIES,
                        "POST": req.POST,
                        "FILES": req.FILES,
                    },
                )()

                try:
                    return await outer.handle_request_async(endpoint, synthetic_request)
                except Http404 as e:
                    error_response = ResourceNotFoundError(
                        " ".join(e.args)
                    ).to_response()
                    return JsonResponse(error_response, status=HTTPStatus.NOT_FOUND)

        else:

            def handle(self, req, **path_params):
                synthetic_request = type(
                    "Request",
                    (),
                    {
                        "path_params": path_params,
                        "GET": req.GET,
                        "body": req.body,
                        "headers": req.headers,
                        "COOKIES": req.COOKIES,
                        "POST": req.POST,
                        "FILES": req.FILES,
                    },
                )()

                try:
                    return outer.handle_request_sync(endpoint, synthetic_request)
                except Http404 as e:
                    error_response = ResourceNotFoundError(
                        " ".join(e.args)
                    ).to_response()
                    return JsonResponse(error_response, status=HTTPStatus.NOT_FOUND)

        setattr(view, method_name, handle)
        return view

    def _get_path_params(self, request) -> dict:
        return getattr(request, "path_params", {})

    def _get_query_params(self, request) -> dict:
        query_params = {}
        for key in request.GET.keys():
            values = request.GET.getlist(key)
            query_params[key] = values[0] if len(values) == 1 else values
        return query_params

    def _get_headers(self, request) -> dict:
        return dict(request.headers)

    def _get_cookies(self, request) -> dict:
        return dict(request.COOKIES)

    def _get_body_sync(self, request) -> dict:
        if hasattr(request, "body") and request.body:
            try:
                return from_json(request.body.decode("utf-8"))
            except Exception:
                pass
        return {}

    async def _get_body_async(self, request) -> dict:
        return self._get_body_sync(request)

    def _get_form_data_sync(self, request) -> dict:
        return dict(request.POST) if hasattr(request, "POST") else {}

    async def _get_form_and_files_async(self, request) -> tuple[dict, dict]:
        return self._get_form_data_sync(request), self._get_files_sync(request)

    def _get_files_sync(self, request) -> dict:
        files = {}
        if hasattr(request, "FILES"):
            for name, file in request.FILES.items():
                # Read file content into temporary file
                import tempfile

                temp_file = tempfile.NamedTemporaryFile(delete=False)
                for chunk in file.chunks():
                    temp_file.write(chunk)
                temp_file.seek(0)

                files[name] = UploadFile(
                    filename=file.name, content_type=file.content_type, file=temp_file
                )
        return files

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

    def _register_docs_endpoints(self):
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
