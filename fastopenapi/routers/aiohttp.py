import functools
import inspect
from collections.abc import Callable

from aiohttp import web

from fastopenapi.base_router import BaseRouter


class AioHttpRouter(BaseRouter):
    def __init__(self, app: web.Application = None, **kwargs):
        self._routes_aiohttp = []
        super().__init__(app, **kwargs)

    @classmethod
    async def _aiohttp_view(cls, request: web.Request, router, endpoint: Callable):
        """
        Handle request routing and parameter resolution for AioHttp
        """
        query_params = dict(request.query)
        body = {}
        try:
            body_bytes = await request.read()
            if body_bytes:
                body = await request.json()
        except Exception:
            pass

        all_params = {**query_params, **request.match_info}
        try:
            kwargs = router.resolve_endpoint_params(endpoint, all_params, body)
        except Exception as e:
            error_response = cls.handle_exception(e)
            return web.json_response(
                error_response, status=getattr(e, "status_code", 422)
            )

        try:
            if inspect.iscoroutinefunction(endpoint):
                result = await endpoint(**kwargs)
            else:
                result = endpoint(**kwargs)
        except Exception as e:
            error_response = cls.handle_exception(e)
            return web.json_response(
                error_response, status=getattr(e, "status_code", 500)
            )

        meta = getattr(endpoint, "__route_meta__", {})
        status_code = meta.get("status_code", 200)
        result = router._serialize_response(result)
        return web.json_response(result, status=status_code)

    def add_route(self, path: str, method: str, endpoint: Callable):
        """
        Add a route to the AioHttp application
        """
        super().add_route(path, method, endpoint)
        view = functools.partial(
            AioHttpRouter._aiohttp_view, router=self, endpoint=endpoint
        )
        if self.app is not None:
            self.app.router.add_route(method.upper(), path, view)
        else:
            self._routes_aiohttp.append((path, method, view))

    def _register_docs_endpoints(self):
        """
        Register OpenAPI, Swagger, and Redoc documentation endpoints
        """

        async def openapi_view(request):
            return web.json_response(self.openapi)

        async def docs_view(request):
            html = self.render_swagger_ui(self.openapi_url)
            return web.Response(text=html, content_type="text/html")

        async def redoc_view(request):
            html = self.render_redoc_ui(self.openapi_url)
            return web.Response(text=html, content_type="text/html")

        if self.app is not None:
            self.app.router.add_route("GET", self.openapi_url, openapi_view)
            self.app.router.add_route("GET", self.docs_url, docs_view)
            self.app.router.add_route("GET", self.redoc_url, redoc_view)
