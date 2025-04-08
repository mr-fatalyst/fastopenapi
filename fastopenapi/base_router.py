import inspect
import re
import typing
from collections.abc import Callable
from http import HTTPStatus
from typing import Any, ClassVar

from pydantic import BaseModel

from fastopenapi.error_handler import (
    BadRequestError,
    ValidationError,
    format_exception_response,
)

SWAGGER_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.20.0/"
REDOC_URL = "https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"

PYTHON_TYPE_MAPPING = {
    int: "integer",
    float: "number",
    bool: "boolean",
    str: "string",
}


class BaseRouter:
    """
    Base router that collects routes and generates an OpenAPI schema.
    This class is extended by specific framework routers to integrate with
    web frameworks.

    Parameters:
    - app: The web framework application instance (e.g., Flask, Falcon, etc.).
    If provided, documentation and schema routes are automatically added to the app.
    - docs_url: URL path prefix where the Swagger documentation UI will be served
    (defaults to "/docs").
    - redoc_url: URL path prefix where the Redoc documentation UI will be served
    (defaults to "/docs").
    - openapi_url: URL path where the OpenAPI JSON schema will be served
    (defaults to "/openapi.json").
    - openapi_version: OpenAPI version for the schema (defaults to "3.0.0").
    - title: Title of the API documentation (defaults to "My App").
    - version: Version of the API (defaults to "0.1.0").
    - description: Description of the API
    (included in OpenAPI info, default "API documentation").

    The BaseRouter allows defining routes using decorator methods (get, post, etc.).
    It can include sub-routers and generate an OpenAPI specification from
    the declared routes.
    """

    # Class-level cache for model schemas to avoid redundant processing
    _model_schema_cache: ClassVar[dict[str, dict]] = {}

    def __init__(
        self,
        app: Any = None,
        docs_url: str = "/docs",
        redoc_url: str = "/redoc",
        openapi_url: str = "/openapi.json",
        openapi_version: str = "3.0.0",
        title: str = "My App",
        version: str = "0.1.0",
        description: str = "API documentation",
    ):
        self.app = app
        self.docs_url = docs_url
        self.redoc_url = redoc_url
        self.openapi_url = openapi_url
        self.openapi_version = openapi_version
        self.title = title
        self.version = version
        self.description = description
        self._routes: list[tuple[str, str, Callable]] = []
        self._openapi_schema = None
        if self.app is not None:
            if self.docs_url and self.redoc_url and self.openapi_url:
                self._register_docs_endpoints()
            else:
                print(
                    "Warning! You didn't set docs_url, redoc_url or openapi_url.\n"
                    "API Documentation will be skipped."
                )

    def add_route(self, path: str, method: str, endpoint: Callable):
        self._routes.append((path, method.upper(), endpoint))

    def include_router(self, other: "BaseRouter", prefix: str | None = None):
        for path, method, endpoint in other.get_routes():
            _path = f"{prefix.rstrip('/')}/{path.lstrip('/')}" if prefix else path
            self.add_route(_path, method, endpoint)

    def get_routes(self):
        return self._routes

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
        info = {
            "title": self.title,
            "version": self.version,
            "description": self.description,
        }

        schema = {
            "openapi": self.openapi_version,
            "info": info,
            "paths": {},
            "components": {"schemas": {}},
        }
        definitions = {}

        # Add standard error responses to components schema
        error_schema = self._generate_error_schema()
        definitions.update(error_schema)

        for path, method, endpoint in self._routes:
            openapi_path = re.sub(r"<(?:\w:)?(\w+)>", r"{\1}", path)
            operation = self._build_operation(
                endpoint, definitions, openapi_path, method
            )
            schema["paths"].setdefault(openapi_path, {})[method.lower()] = operation
        schema["components"]["schemas"].update(definitions)
        return schema

    def _generate_error_schema(self) -> dict[str, Any]:
        """Generate OpenAPI schemas for standard error responses."""
        return {
            "ErrorSchema": {
                "type": "object",
                "properties": {
                    "error": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string"},
                            "message": {"type": "string"},
                            "status": {"type": "integer"},
                            "details": {"type": "string"},
                        },
                        "required": ["type", "message", "status"],
                    }
                },
                "required": ["error"],
            }
        }

    def _build_operation(
        self, endpoint, definitions: dict, route_path: str, http_method: str
    ) -> dict:
        parameters, request_body = self._build_parameters_and_body(
            endpoint, definitions, route_path, http_method
        )

        meta = getattr(endpoint, "__route_meta__", {})
        status_code = str(meta.get("status_code", 200))

        # Build standard responses including error responses
        responses = self._build_responses(meta, definitions, status_code)

        # Add standard error responses
        responses.update(self._build_error_responses(meta))

        op = {
            "summary": endpoint.__doc__ or "",
            "responses": responses,
        }
        if parameters:
            op["parameters"] = parameters
        if request_body:
            op["requestBody"] = request_body
        if meta.get("tags"):
            op["tags"] = meta["tags"]
        return op

    def _build_parameters_and_body(
        self, endpoint, definitions: dict, route_path: str, http_method: str
    ):
        sig = inspect.signature(endpoint)
        parameters = []
        request_body = None

        path_params = {match.group(1) for match in re.finditer(r"{(\w+)}", route_path)}

        for param_name, param in sig.parameters.items():
            if isinstance(param.annotation, type) and issubclass(
                param.annotation, BaseModel
            ):
                if http_method.upper() == "GET":
                    model_schema = param.annotation.model_json_schema()
                    required_fields = model_schema.get("required", [])
                    properties = model_schema.get("properties", {})
                    for prop_name, prop_schema in properties.items():
                        parameters.append(
                            {
                                "name": prop_name,
                                "in": "query",
                                "required": prop_name in required_fields,
                                "schema": prop_schema,
                            }
                        )
                else:
                    model_schema = self._get_model_schema(param.annotation, definitions)
                    request_body = {
                        "content": {"application/json": {"schema": model_schema}},
                        "required": param.default is inspect.Parameter.empty,
                    }
            else:
                location = "path" if param_name in path_params else "query"
                openapi_type = PYTHON_TYPE_MAPPING.get(param.annotation, "string")
                parameters.append(
                    {
                        "name": param_name,
                        "in": location,
                        "required": (param.default is inspect.Parameter.empty)
                        or (location == "path"),
                        "schema": {"type": openapi_type},
                    }
                )

        return parameters, request_body

    def _build_responses(self, meta: dict, definitions: dict, status_code: str) -> dict:
        responses = {status_code: {"description": HTTPStatus(int(status_code)).phrase}}
        response_model = meta.get("response_model")
        if response_model:
            origin = typing.get_origin(response_model)
            if origin is list:
                inner_type = typing.get_args(response_model)[0]
                if isinstance(inner_type, type) and issubclass(inner_type, BaseModel):
                    inner_schema = self._get_model_schema(inner_type, definitions)
                    array_schema = {"type": "array", "items": inner_schema}
                    responses[status_code]["content"] = {
                        "application/json": {"schema": array_schema}
                    }
                else:
                    raise Exception("Incorrect response_model")
            elif isinstance(response_model, type) and issubclass(
                response_model, BaseModel
            ):
                resp_model_schema = self._get_model_schema(response_model, definitions)
                responses[status_code]["content"] = {
                    "application/json": {"schema": resp_model_schema}
                }
            elif response_model in PYTHON_TYPE_MAPPING:
                responses[status_code]["content"] = {
                    "application/json": {
                        "schema": {"type": PYTHON_TYPE_MAPPING[response_model]}
                    }
                }
            else:
                raise Exception("Incorrect response_model")
        return responses

    def _build_error_responses(self, meta) -> dict[str, Any]:
        """Build standard error responses for OpenAPI docs."""
        response_errors = meta.get("response_errors")
        error_ref = {"$ref": "#/components/schemas/ErrorSchema"}
        errors_dict = {
            "400": {
                "description": "Bad Request",
                "content": {"application/json": {"schema": error_ref}},
            },
            "401": {
                "description": "Unauthorized",
                "content": {"application/json": {"schema": error_ref}},
            },
            "403": {
                "description": "Forbidden",
                "content": {"application/json": {"schema": error_ref}},
            },
            "404": {
                "description": "Not Found",
                "content": {"application/json": {"schema": error_ref}},
            },
            "422": {
                "description": "Validation Error",
                "content": {"application/json": {"schema": error_ref}},
            },
            "500": {
                "description": "Internal Server Error",
                "content": {"application/json": {"schema": error_ref}},
            },
        }
        if response_errors:
            return {str(code): errors_dict[str(code)] for code in response_errors}
        else:
            return {}

    def _register_docs_endpoints(self):
        """
        Register documentation and OpenAPI schema endpoints to the app
        (to be implemented in subclasses).
        """
        raise NotImplementedError

    @staticmethod
    def _serialize_response(result: Any) -> Any:
        from pydantic import BaseModel

        if isinstance(result, BaseModel):
            return result.model_dump()
        if isinstance(result, list):
            return [BaseRouter._serialize_response(item) for item in result]
        if isinstance(result, dict):
            return {k: BaseRouter._serialize_response(v) for k, v in result.items()}
        return result

    @classmethod
    def _get_model_schema(cls, model: type[BaseModel], definitions: dict) -> dict:
        """
        Get the OpenAPI schema for a Pydantic model, with caching for better performance
        """
        model_name = model.__name__
        cache_key = f"{model.__module__}.{model_name}"

        # Check if the schema is already in the class-level cache
        if cache_key not in cls._model_schema_cache:
            # Generate the schema if it's not in the cache
            model_schema = model.model_json_schema(
                ref_template="#/components/schemas/{model}"
            )

            # Process and store nested definitions
            for key in ("definitions", "$defs"):
                if key in model_schema:
                    definitions.update(model_schema[key])
                    del model_schema[key]

            # Add schema to the cache
            cls._model_schema_cache[cache_key] = model_schema

        # Make sure the schema is in the definitions dictionary
        if model_name not in definitions:
            definitions[model_name] = cls._model_schema_cache[cache_key]

        return {"$ref": f"#/components/schemas/{model_name}"}

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

    @staticmethod
    def render_redoc_ui(openapi_json_url: str) -> str:
        return f"""
        <!DOCTYPE html>
        <html>
          <head>
            <title>ReDoc</title>
            <meta charset="utf-8"/>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
              body {{
                margin: 0;
                padding: 0;
              }}
            </style>
          </head>
          <body>
            <redoc spec-url='{openapi_json_url}'></redoc>
            <script src="{REDOC_URL}"></script>
          </body>
        </html>
        """

    @staticmethod
    def resolve_endpoint_params(
        endpoint: Callable, all_params: dict, body: dict
    ) -> dict:
        sig = inspect.signature(endpoint)
        kwargs = {}
        for name, param in sig.parameters.items():
            annotation = param.annotation
            is_required = param.default is inspect.Parameter.empty
            if isinstance(annotation, type) and issubclass(annotation, BaseModel):
                try:
                    params = body if body else all_params
                    kwargs[name] = annotation(**params)
                except Exception as e:
                    # Use 422 for Pydantic model validation errors
                    raise ValidationError(
                        f"Validation error for parameter '{name}'", str(e)
                    )
            else:
                if name in all_params:
                    try:
                        kwargs[name] = annotation(all_params[name])
                    except Exception as e:
                        # Use 400 for type conversion errors
                        raise BadRequestError(
                            f"Error parsing parameter '{name}'. "
                            f"Must be a valid {annotation.__name__}",
                            str(e),
                        )
                elif not is_required:
                    kwargs[name] = param.default
                else:
                    # Missing a required parameter is 400
                    raise BadRequestError(f"Missing required parameter: '{name}'")
        return kwargs

    @property
    def openapi(self) -> dict:
        if self._openapi_schema is None:
            self._openapi_schema = self.generate_openapi()
            # We don't need model cache anymore
            self.__class__._model_schema_cache.clear()
        return self._openapi_schema

    @staticmethod
    def handle_exception(exception: Exception) -> dict[str, Any]:
        """
        Process any exception into a standardized error response.
        """
        return format_exception_response(exception)
