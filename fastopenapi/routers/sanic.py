import inspect

from pydantic import BaseModel
from sanic import Sanic, response

from fastopenapi.base_router import BaseRouter


class SanicRouter(BaseRouter):
    def __init__(
        self,
        app: Sanic = None,
        docs_url: str = "/docs/",
        openapi_version: str = "3.0.0",
        title: str = "My Sanic App",
        version: str = "0.1.0",
    ):
        super().__init__(app, docs_url, openapi_version, title, version)
        if self.app is not None:
            self._register_docs_endpoints()

    def add_route(self, path: str, method: str, endpoint):
        super().add_route(path, method, endpoint)

        async def view_func(request, *args, **kwargs):
            params = {
                k: (v[0] if isinstance(v, list) else v) for k, v in request.args.items()
            }
            if request.json:
                params.update(request.json)
            try:
                if inspect.iscoroutinefunction(endpoint):
                    result = await endpoint(**params)
                else:
                    result = endpoint(**params)
            except TypeError as exc:
                return response.json({"detail": str(exc)}, status=422)
            if isinstance(result, BaseModel):
                result = result.model_dump()
            return response.json(result)

        route_name = f"{endpoint.__name__}_{method.lower()}_{path.replace('/', '_')}"
        self.app.add_route(view_func, path, methods=[method.upper()], name=route_name)

    def include_router(self, other: BaseRouter):
        for path, method, endpoint in other.get_routes():
            self.add_route(path, method, endpoint)

    def _register_docs_endpoints(self):
        @self.app.route("/openapi.json", methods=["GET"])
        async def openapi_view(request):
            return response.json(self.generate_openapi())

        @self.app.route(self.docs_url, methods=["GET"])
        async def docs_view(request):
            html = self.render_swagger_ui("/openapi.json")
            return response.html(html)
