import inspect
import json

from pydantic import BaseModel
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route

from fastopenapi.base_router import BaseRouter


class StarletteRouter(BaseRouter):
    def __init__(
        self,
        app: Starlette = None,
        docs_url: str = "/docs/",
        openapi_version: str = "3.0.0",
        title: str = "My Starlette App",
        version: str = "0.1.0",
    ):
        super().__init__(app, docs_url, openapi_version, title, version)
        self._routes_starlette = []
        if self.app is not None:
            self._register_docs_endpoints()

    def add_route(self, path: str, method: str, endpoint):
        super().add_route(path, method, endpoint)
        if self.app is not None:

            async def view(request):
                params = dict(request.query_params)
                try:
                    body = await request.body()
                    if body:
                        json_body = json.loads(body.decode("utf-8"))
                        params.update(json_body)
                except Exception:
                    pass
                try:
                    if inspect.iscoroutinefunction(endpoint):
                        result = await endpoint(**params)
                    else:
                        result = endpoint(**params)
                except TypeError as exc:
                    return JSONResponse({"detail": str(exc)}, status_code=422)
                if isinstance(result, BaseModel):
                    result = result.model_dump()
                return JSONResponse(result)

            self._routes_starlette.append(Route(path, view, methods=[method.upper()]))

    def include_router(self, other: BaseRouter):
        for path, method, endpoint in other.get_routes():
            self.add_route(path, method, endpoint)

    def register_routes(self):
        if self.app is not None:
            self.app.router.routes.extend(self._routes_starlette)

    def _register_docs_endpoints(self):
        async def openapi_view(request):
            return JSONResponse(self.generate_openapi())

        async def docs_view(request):
            html = self.render_swagger_ui("/openapi.json")
            return HTMLResponse(html)

        self.app.router.routes.append(
            Route("/openapi.json", openapi_view, methods=["GET"])
        )
        self.app.router.routes.append(Route(self.docs_url, docs_view, methods=["GET"]))
