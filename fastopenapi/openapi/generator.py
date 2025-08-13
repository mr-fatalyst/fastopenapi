import inspect
import re
import threading
import typing
from functools import lru_cache

from pydantic import BaseModel

from fastopenapi.core.constants import PYTHON_TYPE_MAPPING
from fastopenapi.core.types import Cookie, Form, Header, UploadFile

# Thread-safe compiled regex patterns
PATH_PARAM_PATTERN = re.compile(r"<(?:[^:>]+:)?([^>]+)>")
OPENAPI_PATH_PATTERN = re.compile(r"{(\w+)}")


class OpenAPIGenerator:
    """Generate OpenAPI schema from routes"""

    def __init__(self, router):
        self.router = router
        self.definitions = {}
        # Instance-level cache with thread lock
        self._model_schema_cache = {}
        self._cache_lock = threading.Lock()

    def generate(self) -> dict:
        """Generate complete OpenAPI schema"""
        # Add error schemas
        self._add_error_schemas()

        # Build paths
        paths = {}
        for route in self.router.get_routes():
            openapi_path = self._convert_path(route.path)
            operation = self._build_operation(route)

            if openapi_path not in paths:
                paths[openapi_path] = {}

            paths[openapi_path][route.method.lower()] = operation

        return {
            "openapi": self.router.openapi_version,
            "info": {
                "title": self.router.title,
                "version": self.router.version,
                "description": self.router.description,
            },
            "paths": paths,
            "components": {"schemas": self.definitions},
        }

    @lru_cache(maxsize=128)
    def _convert_path(self, path: str) -> str:
        """Convert path format to OpenAPI format with caching"""
        return PATH_PARAM_PATTERN.sub(r"{\1}", path)

    def _build_operation(self, route) -> dict:
        """Build operation object for a route"""
        parameters, request_body = self._build_parameters_and_body(route)
        responses = self._build_responses(route)

        operation = {
            "summary": route.endpoint.__doc__ or "",
            "responses": responses,
        }

        if parameters:
            operation["parameters"] = parameters
        if request_body:
            operation["requestBody"] = request_body
        if route.meta.get("tags"):
            operation["tags"] = route.meta["tags"]
        if route.meta.get("deprecated"):
            operation["deprecated"] = True

        return operation

    def _build_parameters_and_body(self, route) -> tuple[list, dict]:
        """Build parameters and request body"""
        sig = inspect.signature(route.endpoint)
        parameters = []
        request_body = None

        # Extract path parameters using pre-compiled pattern
        openapi_path = self._convert_path(route.path)
        path_params = set(OPENAPI_PATH_PATTERN.findall(openapi_path))

        for param_name, param in sig.parameters.items():
            # Handle Pydantic models
            if self._is_pydantic_model(param.annotation):
                if route.method == "GET":
                    # For GET, extract as query parameters
                    query_params = self._build_query_params_from_model(param.annotation)
                    parameters.extend(query_params)
                else:
                    # For other methods, use as request body
                    model_schema = self._get_model_schema(param.annotation)
                    request_body = {
                        "content": {"application/json": {"schema": model_schema}},
                        "required": param.default is inspect.Parameter.empty,
                    }
            # Handle file uploads
            elif param.annotation == UploadFile:
                if not request_body:
                    request_body = {
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        param_name: {
                                            "type": "string",
                                            "format": "binary",
                                        }
                                    },
                                }
                            }
                        }
                    }
            # Handle other parameters
            else:
                param_info = self._build_parameter_info(param_name, param, path_params)
                if param_info:
                    parameters.append(param_info)

        return parameters, request_body

    def _build_parameter_info(
        self, param_name: str, param: inspect.Parameter, path_params: set
    ) -> dict:
        """Build parameter info"""
        # Determine location
        if param_name in path_params:
            location = "path"
        elif isinstance(param.default, Header):
            location = "header"
            param_name = param.default.alias or param_name.replace("_", "-")
        elif isinstance(param.default, Cookie):
            location = "cookie"
        elif isinstance(param.default, Form):
            return None  # Form data handled in request body
        else:
            location = "query"

        # Build schema
        schema = self._build_parameter_schema(param.annotation)

        # Determine if required
        is_required = param.default is inspect.Parameter.empty or location == "path"

        return {
            "name": param_name,
            "in": location,
            "required": is_required,
            "schema": schema,
        }

    def _build_parameter_schema(self, annotation) -> dict:
        """Build OpenAPI schema for a parameter"""
        origin = typing.get_origin(annotation)
        if origin is list:
            args = typing.get_args(annotation)
            item_type = "string"
            if args and args[0] in PYTHON_TYPE_MAPPING:
                item_type = PYTHON_TYPE_MAPPING[args[0]]
            return {"type": "array", "items": {"type": item_type}}

        return {"type": PYTHON_TYPE_MAPPING.get(annotation, "string")}

    def _build_responses(self, route) -> dict:
        """Build responses section"""
        from http import HTTPStatus

        status_code = str(route.meta.get("status_code", 200))
        responses = {status_code: {"description": HTTPStatus(int(status_code)).phrase}}

        # Add response model if specified
        response_model = route.meta.get("response_model")
        if response_model:
            origin = typing.get_origin(response_model)
            if origin is list:
                inner_type = typing.get_args(response_model)[0]
                if self._is_pydantic_model(inner_type):
                    inner_schema = self._get_model_schema(inner_type)
                    array_schema = {"type": "array", "items": inner_schema}
                    responses[status_code]["content"] = {
                        "application/json": {"schema": array_schema}
                    }
            elif self._is_pydantic_model(response_model):
                schema = self._get_model_schema(response_model)
                responses[status_code]["content"] = {
                    "application/json": {"schema": schema}
                }

        # Add error responses
        if route.meta.get("response_errors"):
            for error_code in route.meta["response_errors"]:
                responses[str(error_code)] = {
                    "description": HTTPStatus(error_code).phrase,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ErrorSchema"}
                        }
                    },
                }

        return responses

    def _build_query_params_from_model(self, model_class: type[BaseModel]) -> list:
        """Convert Pydantic model fields to query parameters"""
        parameters = []
        model_schema = model_class.model_json_schema(mode="serialization")
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

        return parameters

    def _get_model_schema(self, model: type[BaseModel]) -> dict:
        """Get OpenAPI schema for a Pydantic model with thread-safe caching"""
        model_name = model.__name__
        cache_key = f"{model.__module__}.{model_name}"

        with self._cache_lock:
            if cache_key not in self._model_schema_cache:
                model_schema = model.model_json_schema(
                    mode="serialization",
                    ref_template="#/components/schemas/{model}",
                )

                # Process nested definitions
                for key in ("definitions", "$defs"):
                    if key in model_schema:
                        self.definitions.update(model_schema[key])
                        del model_schema[key]

                self._model_schema_cache[cache_key] = model_schema

            if model_name not in self.definitions:
                self.definitions[model_name] = self._model_schema_cache[cache_key]

        return {"$ref": f"#/components/schemas/{model_name}"}

    def _add_error_schemas(self):
        """Add standard error response schemas"""
        self.definitions["ErrorSchema"] = {
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

    @staticmethod
    def _is_pydantic_model(annotation) -> bool:
        """Check if annotation is a Pydantic model"""
        return isinstance(annotation, type) and issubclass(annotation, BaseModel)
