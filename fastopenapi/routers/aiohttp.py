import functools
from collections.abc import Callable

from aiohttp import web

from fastopenapi.core.types import Response, UploadFile
from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui
from fastopenapi.routers.base import BaseAdapter


class AioHttpRouter(BaseAdapter):
    """AioHttp adapter for FastOpenAPI"""

    def __init__(self, app: web.Application = None, **kwargs):
        super().__init__(app, **kwargs)

    def add_route(self, path: str, method: str, endpoint: Callable):
        """Add route to AioHttp application"""
        super().add_route(path, method, endpoint)

        if self.app is not None:
            view = functools.partial(self._aiohttp_view, router=self, endpoint=endpoint)
            self.app.router.add_route(method.upper(), path, view)

    @staticmethod
    async def _aiohttp_view(request: web.Request, router, endpoint: Callable):
        """Handle AioHttp request"""
        if router.is_async_endpoint(endpoint):
            return await router.handle_request_async(endpoint, request)
        else:
            return router.handle_request_sync(endpoint, request)

    def _get_path_params(self, request: web.Request) -> dict:
        return dict(request.match_info)

    def _get_query_params(self, request: web.Request) -> dict:
        query_params = {}
        for key in request.query:
            values = request.query.getall(key)
            query_params[key] = values[0] if len(values) == 1 else values
        return query_params

    def _get_headers(self, request: web.Request) -> dict:
        return dict(request.headers)

    def _get_cookies(self, request: web.Request) -> dict:
        return dict(request.cookies)

    def _get_body_sync(self, request: web.Request) -> dict:
        # Sync endpoints in aiohttp can't read body
        return {}

    async def _get_body_async(self, request: web.Request) -> dict:
        try:
            body_bytes = await request.read()
            if body_bytes:
                return await request.json()
        except Exception:
            pass
        return {}

    def _get_form_data_sync(self, request: web.Request) -> dict:
        # Sync endpoints in aiohttp can't read form data
        return {}

    def _get_files_sync(self, request: web.Request) -> dict:
        # Sync endpoints in aiohttp can't read files
        return {}

    async def _get_form_and_files_async(
        self, request: web.Request
    ) -> tuple[dict, dict]:
        form_data = {}
        files = {}

        if request.content_type == "multipart/form-data":
            reader = await request.multipart()
            async for part in reader:
                if part.filename:
                    # Stream file to temporary file instead of loading into memory
                    import tempfile

                    temp_file = tempfile.NamedTemporaryFile(delete=False)

                    # Stream chunks to avoid memory issues
                    async for chunk in part:
                        temp_file.write(chunk)

                    temp_file.seek(0)
                    files[part.name] = UploadFile(
                        filename=part.filename,
                        content_type=part.headers.get("Content-Type", ""),
                        file=temp_file,
                    )
                else:
                    form_data[part.name] = await part.text()

        return form_data, files

    def build_framework_response(self, response: Response) -> web.Response:
        """Build AioHttp response"""
        return web.json_response(
            response.content, status=response.status_code, headers=response.headers
        )

    def _register_docs_endpoints(self):
        """Register documentation endpoints"""

        async def openapi_view(request):
            return web.json_response(self.openapi)

        async def docs_view(request):
            html = render_swagger_ui(self.openapi_url)
            return web.Response(text=html, content_type="text/html")

        async def redoc_view(request):
            html = render_redoc_ui(self.openapi_url)
            return web.Response(text=html, content_type="text/html")

        if self.app is not None:
            self.app.router.add_route("GET", self.openapi_url, openapi_view)
            self.app.router.add_route("GET", self.docs_url, docs_view)
            self.app.router.add_route("GET", self.redoc_url, redoc_view)
