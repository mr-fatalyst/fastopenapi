import functools
import inspect
from collections.abc import Callable

from pydantic_core import from_json
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route

from fastopenapi.core.types import RequestData, Response, UploadFile
from fastopenapi.errors.handler import format_exception_response
from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui
from fastopenapi.routers.base import BaseAdapter


class StarletteRouter(BaseAdapter):
    """Starlette adapter for FastOpenAPI"""

    def __init__(self, app: Starlette = None, **kwargs):
        self._routes_starlette = []
        super().__init__(app, **kwargs)

    def add_route(self, path: str, method: str, endpoint: Callable):
        """Add route to Starlette application"""
        super().add_route(path, method, endpoint)

        view = functools.partial(self._starlette_view, router=self, endpoint=endpoint)
        route = Route(path, view, methods=[method.upper()])

        if self.app is not None:
            self.app.router.routes.append(route)
        else:
            self._routes_starlette.append(route)

    @staticmethod
    async def _starlette_view(request, router, endpoint):
        """Handle Starlette request"""
        try:
            request_data = await router.extract_request_data_async(request)
            kwargs = router.resolver.resolve(endpoint, request_data)

            # Call endpoint
            if inspect.iscoroutinefunction(endpoint):
                result = await endpoint(**kwargs)
            else:
                result = endpoint(**kwargs)

            response = router.response_builder.build(result, endpoint.__route_meta__)
            return router.build_framework_response(response)

        except Exception as e:
            error_response = format_exception_response(e)
            return JSONResponse(
                error_response, status_code=getattr(e, "status_code", 500)
            )

    async def extract_request_data_async(self, request) -> RequestData:
        """Extract data from Starlette request (async)"""
        # Query parameters
        query_params = {}
        for key in request.query_params:
            values = request.query_params.getlist(key)
            query_params[key] = values[0] if len(values) == 1 else values

        # Headers (normalize to lowercase)
        headers = {k.lower(): v for k, v in request.headers.items()}

        # Cookies
        cookies = dict(request.cookies)

        # Body
        body = {}
        try:
            body_bytes = await request.body()
            if body_bytes:
                body = from_json(body_bytes.decode("utf-8"))
        except Exception:
            pass

        # Form data and files
        form_data = {}
        files = {}
        if request.headers.get("content-type", "").startswith("multipart/form-data"):
            form = await request.form()
            for key, value in form.items():
                if hasattr(value, "filename"):
                    # This is a file
                    files[key] = UploadFile(
                        filename=value.filename,
                        content_type=value.content_type,
                        file=value.file,
                    )
                else:
                    form_data[key] = value

        return RequestData(
            path_params=dict(request.path_params),
            query_params=query_params,
            headers=headers,
            cookies=cookies,
            body=body,
            form_data=form_data,
            files=files,
        )

    def extract_request_data(self, request) -> RequestData:
        """Not used in async adapter"""
        raise NotImplementedError("Use extract_request_data_async")

    def build_framework_response(self, response: Response) -> JSONResponse:
        """Build Starlette response"""
        return JSONResponse(
            response.content, status_code=response.status_code, headers=response.headers
        )

    def _register_docs_endpoints(self):
        """Register documentation endpoints"""

        async def openapi_view(request):
            return JSONResponse(self.openapi)

        async def docs_view(request):
            html = render_swagger_ui(self.openapi_url)
            return HTMLResponse(html)

        async def redoc_view(request):
            html = render_redoc_ui(self.openapi_url)
            return HTMLResponse(html)

        self.app.router.routes.append(
            Route(self.openapi_url, openapi_view, methods=["GET"])
        )
        self.app.router.routes.append(Route(self.docs_url, docs_view, methods=["GET"]))
        self.app.router.routes.append(
            Route(self.redoc_url, redoc_view, methods=["GET"])
        )
