import functools
from collections.abc import Callable

from pydantic_core import from_json
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route

from fastopenapi.core.types import Response, UploadFile
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
        if router.is_async_endpoint(endpoint):
            return await router.handle_request_async(endpoint, request)
        else:
            return router.handle_request_sync(endpoint, request)

    def _get_path_params(self, request) -> dict:
        return dict(request.path_params)

    def _get_query_params(self, request) -> dict:
        query_params = {}
        for key in request.query_params:
            values = request.query_params.getlist(key)
            query_params[key] = values[0] if len(values) == 1 else values
        return query_params

    def _get_headers(self, request) -> dict:
        return dict(request.headers)

    def _get_cookies(self, request) -> dict:
        return dict(request.cookies)

    def _get_body_sync(self, request) -> dict:
        # Sync endpoints in Starlette can't read body
        return {}

    async def _get_body_async(self, request) -> dict:
        try:
            body_bytes = await request.body()
            if body_bytes:
                return from_json(body_bytes.decode("utf-8"))
        except Exception:
            pass
        return {}

    def _get_form_data_sync(self, request) -> dict:
        # Sync endpoints in Starlette can't read form data
        return {}

    def _get_files_sync(self, request) -> dict:
        # Sync endpoints in Starlette can't read files
        return {}

    async def _get_form_and_files_async(self, request) -> tuple[dict, dict]:
        form_data = {}
        files = {}

        if request.headers.get("content-type", "").startswith("multipart/form-data"):
            form = await request.form()
            for key, value in form.items():
                if hasattr(value, "filename"):
                    # Stream file content to temporary file
                    import tempfile

                    temp_file = tempfile.NamedTemporaryFile(delete=False)

                    # Read in chunks to avoid memory issues
                    while chunk := await value.read(1024 * 1024):  # 1MB chunks
                        temp_file.write(chunk)

                    temp_file.seek(0)
                    files[key] = UploadFile(
                        filename=value.filename,
                        content_type=value.content_type,
                        file=temp_file,
                    )
                else:
                    form_data[key] = value

        return form_data, files

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
