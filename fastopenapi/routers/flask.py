from flask import Flask, Response, jsonify, request
from pydantic import BaseModel

from fastopenapi.base_router import BaseRouter


class FlaskRouter(BaseRouter):
    def __init__(
        self,
        app: Flask = None,
        docs_url: str = "/docs/",
        openapi_version: str = "3.0.0",
        title: str = "My Flask App",
        version: str = "0.1.0",
    ):
        super().__init__(app, docs_url, openapi_version, title, version)
        if self.app is not None:
            self._register_docs_endpoints()

    def add_route(self, path: str, method: str, endpoint):
        super().add_route(path, method, endpoint)
        if self.app is not None:

            def view_func(**kwargs):
                json_data = request.get_json(silent=True) or {}
                params = {**request.args.to_dict(), **json_data}
                try:
                    result = endpoint(**params)
                except TypeError as exc:
                    return jsonify({"detail": str(exc)}), 422
                if isinstance(result, BaseModel):
                    result = result.model_dump()
                return jsonify(result)

            self.app.add_url_rule(
                path, endpoint.__name__, view_func, methods=[method.upper()]
            )

    def include_router(self, other: BaseRouter):
        for path, method, endpoint in other.get_routes():
            self.add_route(path, method, endpoint)

    def _register_docs_endpoints(self):
        @self.app.route("/openapi.json", methods=["GET"])
        def openapi_view():
            return jsonify(self.generate_openapi())

        @self.app.route(self.docs_url, methods=["GET"])
        def docs_view():
            html = self.render_swagger_ui("/openapi.json")
            return Response(html, mimetype="text/html")
