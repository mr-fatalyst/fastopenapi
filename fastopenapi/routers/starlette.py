import functools
import inspect
import json
from collections.abc import Callable

from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route

from fastopenapi.base_router import BaseRouter


class StarletteRouter(BaseRouter):
    def __init__(self, app: Starlette = None, **kwargs):
        self._routes_starlette = []
        super().__init__(app, **kwargs)

    @classmethod
    async def _starlette_view(cls, request, router, endpoint):
        query_params = dict(request.query_params)
        body = {}
        try:
            body_bytes = await request.body()
            if body_bytes:
                body = json.loads(body_bytes.decode("utf-8"))
        except Exception:
            pass
        all_params = {**query_params, **request.path_params}
        try:
            kwargs = router.resolve_endpoint_params(endpoint, all_params, body)
        except Exception as e:
            error_response = cls.handle_exception(e)
            return JSONResponse(
                error_response, status_code=getattr(e, "status_code", 422)
            )
        try:
            if inspect.iscoroutinefunction(endpoint):
                result = await endpoint(**kwargs)
            else:
                result = endpoint(**kwargs)
        except Exception as e:
            error_response = cls.handle_exception(e)
            return JSONResponse(
                error_response, status_code=getattr(e, "status_code", 500)
            )

        meta = getattr(endpoint, "__route_meta__", {})
        status_code = meta.get("status_code", 200)
        result = router._serialize_response(result)
        return JSONResponse(result, status_code=status_code)

    def add_route(self, path: str, method: str, endpoint: Callable):
        super().add_route(path, method, endpoint)
        view = functools.partial(
            StarletteRouter._starlette_view, router=self, endpoint=endpoint
        )
        route = Route(path, view, methods=[method.upper()])
        if self.app is not None:
            self.app.router.routes.append(route)
        else:
            self._routes_starlette.append(route)

    def _register_docs_endpoints(self):
        async def openapi_view(request):
            return JSONResponse(self.openapi)

        async def docs_view(request):
            html = self.render_swagger_ui(self.openapi_url)
            return HTMLResponse(html)

        async def redoc_view(request):
            html = self.render_redoc_ui(self.openapi_url)
            return HTMLResponse(html)

        self.app.router.routes.append(
            Route(self.openapi_url, openapi_view, methods=["GET"])
        )
        self.app.router.routes.append(Route(self.docs_url, docs_view, methods=["GET"]))
        self.app.router.routes.append(
            Route(self.redoc_url, redoc_view, methods=["GET"])
        )
