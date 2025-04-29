import json
import re
from collections.abc import Callable
from http import HTTPStatus

from django.http import Http404, HttpResponse, JsonResponse
from django.urls import path as django_path
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from fastopenapi.base_router import BaseRouter
from fastopenapi.error_handler import ResourceNotFoundError


class DjangoRouter(BaseRouter):
    def __init__(self, app: bool | None = None, **kwargs):
        self._views = {}
        super().__init__(app, **kwargs)

    def add_route(self, path: str, method: str, endpoint: Callable):
        super().add_route(path, method, endpoint)
        self._create_or_update_view(path, method, endpoint)

    def _create_or_update_view(self, path: str, method: str, endpoint: Callable):
        view = self._views.get(path)
        if not view:
            view = type("DynamicView", (View,), {})
            self._views[path] = view
        method_name = method.lower()

        outer = self

        @csrf_exempt
        def handle(self, req, **path_params):
            return outer._handle_request(endpoint, req, **path_params)

        setattr(view, method_name, handle)
        return view

    def _handle_request(self, endpoint, req, **path_params):
        meta = getattr(endpoint, "__route_meta__", {})
        status_code = meta.get("status_code", 200)
        all_params = {**path_params}
        for key in req.GET.keys():
            values = req.GET.getlist(key)
            all_params[key] = values[0] if len(values) == 1 else values
        body = self._read_body(req)
        try:
            kwargs = self.resolve_endpoint_params(endpoint, all_params, body)
        except Exception as e:
            error_response = self.handle_exception(e)
            return JsonResponse(error_response, status=getattr(e, "status_code", 422))
        try:
            result = endpoint(**kwargs)
        except Http404 as e:
            error_response = ResourceNotFoundError(" ".join(e.args)).to_response()
            return JsonResponse(error_response, status=HTTPStatus.NOT_FOUND)
        except Exception as e:
            error_response = self.handle_exception(e)
            return JsonResponse(error_response, status=getattr(e, "status_code", 500))
        result = self._serialize_response(result)
        response = HttpResponse(status=status_code)
        if result:
            json.dump(result, response)
            response.headers["Content-Type"] = "application/json"
        return response

    def _read_body(self, req):
        try:
            body_bytes = req.read()
            if body_bytes:
                return json.loads(body_bytes.decode("utf-8"))
        except Exception:
            pass
        return {}

    def _register_docs_endpoints(self):
        outer = self

        class OpenAPISchemaView(View):
            @csrf_exempt
            def get(self, req):
                return JsonResponse(outer.openapi)

        self._views[self.openapi_url] = OpenAPISchemaView

        class SwaggerUIView(View):
            def get(self, req):
                return HttpResponse(
                    outer.render_swagger_ui(outer.openapi_url).encode(),
                    content_type="text/html",
                )

        class RedocUIView(View):
            def get(self, req):
                return HttpResponse(
                    outer.render_redoc_ui(outer.openapi_url).encode(),
                    content_type="text/html",
                )

        self._views[self.docs_url] = SwaggerUIView
        self._views[self.redoc_url] = RedocUIView

    @property
    def urls(self):
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
