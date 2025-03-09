import re

from flask import Response, jsonify, request
from pydantic import BaseModel
from werkzeug.exceptions import HTTPException

from fastopenapi.base_router import BaseRouter


class FlaskRouter(BaseRouter):
    @staticmethod
    def handle_http_exception(e):
        response = e.get_response()
        response.data = jsonify(
            {"code": e.code, "name": e.name, "description": e.description}
        ).get_data(as_text=True)
        response.content_type = "application/json"
        return response

    def add_route(self, path: str, method: str, endpoint):
        super().add_route(path, method, endpoint)

        if self.app is not None:
            flask_path = re.sub(r"{(\w+)}", r"<\1>", path)

            def view_func(**path_params):
                json_data = request.get_json(silent=True) or {}
                query_params = request.args.to_dict()
                all_params = {**query_params, **path_params}
                body = json_data
                try:
                    kwargs = self.resolve_endpoint_params(endpoint, all_params, body)
                except Exception as e:
                    return jsonify({"detail": str(e)}), 422
                try:
                    result = endpoint(**kwargs)
                except Exception as e:
                    if isinstance(e, HTTPException):
                        return self.handle_http_exception(e)
                    return jsonify({"detail": str(e)}), 422

                meta = getattr(endpoint, "__route_meta__", {})
                status_code = meta.get("status_code", 200)

                if isinstance(result, BaseModel):
                    result = result.model_dump()
                elif isinstance(result, list):
                    result = [
                        item.model_dump() if isinstance(item, BaseModel) else item
                        for item in result
                    ]
                return jsonify(result), status_code

            self.app.add_url_rule(
                flask_path, endpoint.__name__, view_func, methods=[method.upper()]
            )

    def _register_docs_endpoints(self):
        @self.app.route("/openapi.json", methods=["GET"])
        def openapi_view():
            return jsonify(self.openapi)

        @self.app.route(self.docs_url, methods=["GET"])
        def docs_view():
            html = self.render_swagger_ui("/openapi.json")
            return Response(html, mimetype="text/html")
