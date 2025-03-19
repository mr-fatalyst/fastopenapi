import inspect
import re
from collections.abc import Callable

from sanic import response
from sanic.exceptions import HTTPException

from fastopenapi.base_router import BaseRouter


class SanicRouter(BaseRouter):
    @staticmethod
    async def handle_exceptions(request, exception):
        return response.json(
            {
                "description": exception.args[0] if exception.args else "Error",
                "status": (
                    exception.status_code if hasattr(exception, "status_code") else 500
                ),
                "message": str(exception),
            },
            status=exception.status_code if hasattr(exception, "status_code") else 500,
        )

    def add_route(self, path: str, method: str, endpoint: Callable):
        super().add_route(path, method, endpoint)
        if self.app is None:
            return

        sanic_path = re.sub(r"{(\w+)}", r"<\1>", path)

        async def view_func(request, **path_params):
            query_params = {
                k: (v[0] if isinstance(v, list) else v) for k, v in request.args.items()
            }
            json_body = request.json or {}
            all_params = {**query_params, **path_params}
            body = json_body
            try:
                kwargs = self.resolve_endpoint_params(endpoint, all_params, body)
            except Exception as e:
                return response.json({"detail": str(e)}, status=422)
            try:
                if inspect.iscoroutinefunction(endpoint):
                    result = await endpoint(**kwargs)
                else:
                    result = endpoint(**kwargs)
            except Exception as e:
                if isinstance(e, HTTPException):
                    return await self.handle_exceptions(request, e)
                return response.json({"detail": str(e)}, status=500)

            meta = getattr(endpoint, "__route_meta__", {})
            status_code = meta.get("status_code", 200)
            result = self._serialize_response(result)
            return response.json(result, status=status_code)

        route_name = f"{endpoint.__name__}_{method.lower()}_{path.replace('/', '_')}"
        self.app.add_route(
            view_func, sanic_path, methods=[method.upper()], name=route_name
        )

    def _register_docs_endpoints(self):
        @self.app.route(self.openapi_url, methods=["GET"])
        async def openapi_view(request):
            return response.json(self.openapi)

        @self.app.route(self.docs_url, methods=["GET"])
        async def docs_view(request):
            html = self.render_swagger_ui(self.openapi_url)
            return response.html(html)

        @self.app.route(self.redoc_url, methods=["GET"])
        async def redoc_view(request):
            html = self.render_redoc_ui(self.openapi_url)
            return response.html(html)
