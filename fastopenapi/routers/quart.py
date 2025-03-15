import inspect
import re
from collections.abc import Callable

from quart import Response, jsonify, request
from werkzeug.exceptions import HTTPException

from fastopenapi.base_router import BaseRouter


class QuartRouter(BaseRouter):
    @staticmethod
    async def handle_http_exception(e):
        response = e.get_response()
        response.data = await jsonify(
            {"code": e.code, "name": e.name, "description": e.description}
        ).get_data(as_text=True)
        response.content_type = "application/json"
        return response

    def add_route(self, path: str, method: str, endpoint: Callable):
        super().add_route(path, method, endpoint)
        if self.app is not None:
            quart_path = re.sub(r"{(\w+)}", r"<\1>", path)

            async def view_func(**path_params):
                json_data = await request.get_json(silent=True) or {}
                query_params = request.args.to_dict()
                all_params = {**query_params, **path_params}
                body = json_data
                try:
                    kwargs = self.resolve_endpoint_params(endpoint, all_params, body)
                except Exception as e:
                    return jsonify({"detail": str(e)}), 422
                try:
                    if inspect.iscoroutinefunction(endpoint):
                        result = await endpoint(**kwargs)
                    else:
                        result = endpoint(**kwargs)
                except Exception as e:
                    if isinstance(e, HTTPException):
                        return await self.handle_http_exception(e)
                    return jsonify({"detail": str(e)}), 422

                meta = getattr(endpoint, "__route_meta__", {})
                status_code = meta.get("status_code", 200)
                result = self._serialize_response(result)
                return jsonify(result), status_code

            self.app.add_url_rule(
                quart_path, endpoint.__name__, view_func, methods=[method.upper()]
            )

    def _register_docs_endpoints(self):
        @self.app.route(self.openapi_url, methods=["GET"])
        async def openapi_view():
            return jsonify(self.openapi)

        @self.app.route(self.docs_url, methods=["GET"])
        async def docs_view():
            html = self.render_swagger_ui(self.openapi_url)
            return Response(html, mimetype="text/html")

        @self.app.route(self.redoc_url, methods=["GET"])
        async def redoc_view():
            html = self.render_redoc_ui(self.openapi_url)
            return Response(html, mimetype="text/html")
