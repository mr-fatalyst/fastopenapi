import re
from collections.abc import Callable
from http import HTTPStatus

from django.http import Http404, HttpResponse, JsonResponse
from django.urls import path as django_path
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from pydantic_core import from_json, to_json

from fastopenapi.core.types import RequestData, Response, UploadFile
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

        def handle(self, req, **path_params):
            # Create synthetic request object
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
            return outer.handle_django_request(endpoint, synthetic_request)

        setattr(view, method_name, handle)
        return view

    def handle_django_request(self, endpoint: Callable, request) -> HttpResponse:
        """Handle Django-specific request"""
        try:
            request_data = self.extract_request_data(request)
            kwargs = self.resolver.resolve(endpoint, request_data)

            result = endpoint(**kwargs)

            response = self.response_builder.build(result, endpoint.__route_meta__)
            return self.build_framework_response(response)

        except Http404 as e:
            error_response = ResourceNotFoundError(" ".join(e.args)).to_response()
            return JsonResponse(error_response, status=HTTPStatus.NOT_FOUND)
        except Exception as e:
            from fastopenapi.errors.handler import format_exception_response

            error_response = format_exception_response(e)
            return JsonResponse(error_response, status=getattr(e, "status_code", 500))

    def extract_request_data(self, request) -> RequestData:
        """Extract data from Django request"""
        # Query parameters
        query_params = {}
        for key in request.GET.keys():
            values = request.GET.getlist(key)
            query_params[key] = values[0] if len(values) == 1 else values

        # Headers (normalize to lowercase)
        headers = {k.lower(): v for k, v in request.headers.items()}

        # Cookies
        cookies = dict(request.COOKIES)

        # Body
        body = {}
        if hasattr(request, "body") and request.body:
            try:
                body = from_json(request.body.decode("utf-8"))
            except Exception:
                pass

        # Form data
        form_data = dict(request.POST) if hasattr(request, "POST") else {}

        # Files
        files = {}
        if hasattr(request, "FILES"):
            for name, file in request.FILES.items():
                files[name] = UploadFile(
                    filename=file.name, content_type=file.content_type, file=file
                )

        return RequestData(
            path_params=getattr(request, "path_params", {}),
            query_params=query_params,
            headers=headers,
            cookies=cookies,
            body=body,
            form_data=form_data,
            files=files,
        )

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

        # Add custom headers
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
