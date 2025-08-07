import functools
import inspect
from collections.abc import Callable

from pydantic_core import from_json
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route

from fastopenapi.core.types import RequestData, Response, UploadFile
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
        # Check if endpoint is async and use appropriate handler
        if inspect.iscoroutinefunction(endpoint):
            return await router.handle_request_async(endpoint, request)
        else:
            return router.handle_request_sync(endpoint, request)

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
        """Sync extraction for sync endpoints - simplified version"""
        # Query parameters
        query_params = {}
        for key in request.query_params:
            values = request.query_params.getlist(key)
            query_params[key] = values[0] if len(values) == 1 else values

        # Headers (normalize to lowercase)
        headers = {k.lower(): v for k, v in request.headers.items()}

        # Cookies
        cookies = dict(request.cookies)

        return RequestData(
            path_params=dict(request.path_params),
            query_params=query_params,
            headers=headers,
            cookies=cookies,
            body={},  # Body requires async reading
            form_data={},
            files={},
        )

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
