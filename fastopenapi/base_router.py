import inspect
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

SWAGGER_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.20.0/"


class BaseRouter:
    def __init__(
        self,
        app: Any = None,
        docs_url: str = "/docs/",
        openapi_version: str = "3.0.0",
        title: str = "My App",
        version: str = "0.1.0",
    ):
        self.app = app
        self.docs_url = docs_url
        self.openapi_version = openapi_version
        self.title = title
        self.version = version
        self._routes: list[tuple[str, str, Callable]] = []

    def add_route(self, path: str, method: str, endpoint: Callable):
        self._routes.append((path, method.upper(), endpoint))

    def get_routes(self):
        return self._routes

    def include_router(self, other: "BaseRouter"):
        self._routes.extend(other.get_routes())

    def get(self, path: str, **meta):
        def decorator(func: Callable):
            func.__route_meta__ = meta
            self.add_route(path, "GET", func)
            return func

        return decorator

    def post(self, path: str, **meta):
        def decorator(func: Callable):
            func.__route_meta__ = meta
            self.add_route(path, "POST", func)
            return func

        return decorator

    def put(self, path: str, **meta):
        def decorator(func: Callable):
            func.__route_meta__ = meta
            self.add_route(path, "PUT", func)
            return func

        return decorator

    def patch(self, path: str, **meta):
        def decorator(func: Callable):
            func.__route_meta__ = meta
            self.add_route(path, "PATCH", func)
            return func

        return decorator

    def delete(self, path: str, **meta):
        def decorator(func: Callable):
            func.__route_meta__ = meta
            self.add_route(path, "DELETE", func)
            return func

        return decorator

    def generate_openapi(self) -> dict:
        schema = {
            "openapi": self.openapi_version,
            "info": {"title": self.title, "version": self.version},
            "paths": {},
            "components": {"schemas": {}},
        }
        definitions = {}

        for path, method, endpoint in self._routes:
            operation = self._build_operation(endpoint, definitions)
            schema["paths"].setdefault(path, {})[method.lower()] = operation

        schema["components"]["schemas"].update(definitions)
        return schema

    def _build_operation(self, endpoint, definitions: dict) -> dict:
        sig = inspect.signature(endpoint)
        parameters = []
        request_body = None

        for param_name, param in sig.parameters.items():
            if param.annotation is inspect.Parameter.empty:
                continue

            if isinstance(param.annotation, type) and issubclass(
                param.annotation, BaseModel
            ):
                model_schema = self._get_model_schema(param.annotation, definitions)
                request_body = {
                    "content": {"application/json": {"schema": model_schema}},
                    "required": True,
                }
            else:
                parameters.append(
                    {
                        "name": param_name,
                        "in": "query",
                        "required": param.default is inspect.Parameter.empty,
                        "schema": {"type": "string"},
                    }
                )

        op = {
            "summary": endpoint.__doc__ or "",
            "responses": {"200": {"description": "OK"}},
        }
        if parameters:
            op["parameters"] = parameters
        if request_body:
            op["requestBody"] = request_body

        meta = getattr(endpoint, "__route_meta__", {})
        if meta.get("tags"):
            op["tags"] = meta["tags"]
        if meta.get("status_code"):
            code = str(meta["status_code"])
            op["responses"] = {code: {"description": "OK"}}
            response_model = meta.get("response_model")
            if (
                response_model
                and isinstance(response_model, type)
                and issubclass(response_model, BaseModel)
            ):
                resp_model_schema = self._get_model_schema(response_model, definitions)
                op["responses"][code]["content"] = {
                    "application/json": {"schema": resp_model_schema}
                }
        return op

    @staticmethod
    def _get_model_schema(model: type[BaseModel], definitions: dict) -> dict:
        model_schema = model.model_json_schema(
            ref_template="#/components/schemas/{model}"
        )
        for key in ("definitions", "$defs"):
            if key in model_schema:
                definitions.update(model_schema[key])
                del model_schema[key]
        return model_schema

    @staticmethod
    def render_swagger_ui(openapi_json_url: str) -> str:
        return f"""
        <!DOCTYPE html>
        <html lang="en">
          <head>
            <meta charset="UTF-8">
            <title>Swagger UI</title>
            <link rel="stylesheet" href="{SWAGGER_URL}swagger-ui.css" />
          </head>
          <body>
            <div id="swagger-ui"></div>
            <script src="{SWAGGER_URL}swagger-ui-bundle.js"></script>
            <script>
              SwaggerUIBundle({{
                url: '{openapi_json_url}',
                dom_id: '#swagger-ui'
              }});
            </script>
          </body>
        </html>
        """
