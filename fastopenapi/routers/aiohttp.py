import functools
import inspect
from collections.abc import Callable

from aiohttp import web

from fastopenapi.core.types import RequestData, Response, UploadFile
from fastopenapi.errors.handler import format_exception_response
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
            return web.json_response(
                error_response, status=getattr(e, "status_code", 500)
            )

    async def extract_request_data_async(self, request: web.Request) -> RequestData:
        """Extract data from AioHttp request (async)"""
        # Query parameters
        query_params = {}
        for key in request.query:
            values = request.query.getall(key)
            query_params[key] = values[0] if len(values) == 1 else values

        # Headers (normalize to lowercase)
        headers = {k.lower(): v for k, v in request.headers.items()}

        # Cookies
        cookies = dict(request.cookies)

        # Body
        body = {}
        try:
            body_bytes = await request.read()
            if body_bytes:
                body = await request.json()
        except Exception:
            pass

        # Form data and files
        form_data = {}
        files = {}
        if request.content_type == "multipart/form-data":
            reader = await request.multipart()
            async for part in reader:
                if part.filename:
                    # This is a file
                    content = await part.read()
                    files[part.name] = UploadFile(
                        filename=part.filename,
                        content_type=part.headers.get("Content-Type", ""),
                        file=content,  # Store as bytes for simplicity
                    )
                else:
                    # Regular form field
                    form_data[part.name] = await part.text()

        return RequestData(
            path_params=dict(request.match_info),
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
