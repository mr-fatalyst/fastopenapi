import inspect
import re
import threading
import typing
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from pydantic import BaseModel

from fastopenapi.core.constants import PYTHON_TYPE_MAPPING, ParameterSource
from fastopenapi.core.params import (
    BaseParam,
    Body,
    Depends,
    File,
    Form,
    Header,
    Param,
    Security,
)

# Thread-safe compiled regex patterns
PATH_PARAM_PATTERN = re.compile(r"<(?:[^:>]+:)?([^>]+)>")
OPENAPI_PATH_PATTERN = re.compile(r"{(\w+)}")


@dataclass
class ParameterInfo:
    """Data class for parameter information"""

    name: str
    location: str
    schema: dict
    required: bool = False
    description: str | None = None
    examples: dict | None = None
    deprecated: bool = False


class SchemaBuilder:
    """Helper class for building OpenAPI schemas"""

    def __init__(self, definitions: dict, cache_lock: threading.Lock):
        self.definitions = definitions
        self._cache_lock = cache_lock
        self._model_schema_cache = {}

    def build_parameter_schema(self, annotation) -> dict:
        """Build OpenAPI schema for a parameter annotation"""
        origin = typing.get_origin(annotation)

        if origin is list:
            return self._build_array_schema(annotation)

        if origin is typing.Union:
            return self._build_union_schema(annotation)

        return {"type": PYTHON_TYPE_MAPPING.get(annotation, "string")}

    def _build_array_schema(self, annotation) -> dict:
        """Build schema for array types"""
        args = typing.get_args(annotation)
        item_type = "string"
        if args and args[0] in PYTHON_TYPE_MAPPING:
            item_type = PYTHON_TYPE_MAPPING[args[0]]
        return {"type": "array", "items": {"type": item_type}}

    def _build_union_schema(self, annotation) -> dict:
        """Build schema for Union types (including Optional)"""
        args = typing.get_args(annotation)
        if type(None) in args:
            # It's Optional[T]
            non_none_args = [arg for arg in args if arg is not type(None)]
            if non_none_args:
                schema = self.build_parameter_schema(non_none_args[0])
                schema["nullable"] = True
                return schema
        return {"type": "string"}

    def build_parameter_schema_from_param(self, param: inspect.Parameter) -> dict:
        """Build OpenAPI schema from Param object with full constraint support"""
        param_obj = param.default
        annotation = (
            param.annotation if param.annotation != inspect.Parameter.empty else str
        )

        schema = self.build_parameter_schema(annotation)

        if isinstance(param_obj, BaseParam):
            self._apply_param_constraints(schema, param_obj)

        return schema

    def _apply_param_constraints(self, schema: dict, param_obj: Param) -> None:
        """Apply validation constraints from Param object to schema"""
        self._apply_metadata_constraints(schema, param_obj)
        self._apply_object_metadata(schema, param_obj)
        self._apply_default_value(schema, param_obj)

    def _apply_metadata_constraints(self, schema: dict, param_obj: Param) -> None:
        """Apply constraints from param metadata"""
        if not (hasattr(param_obj, "metadata") and param_obj.metadata):
            return

        constraint_mapping = {
            "MinLen": ("min_length", "minLength"),
            "MaxLen": ("max_length", "maxLength"),
            "Ge": ("ge", "minimum"),
            "Le": ("le", "maximum"),
            "Gt": ("gt", "exclusiveMinimum"),
            "Lt": ("lt", "exclusiveMaximum"),
            "MultipleOf": ("multiple_of", "multipleOf"),
        }

        for constraint in param_obj.metadata:
            constraint_type = type(constraint).__name__

            if constraint_type in constraint_mapping:
                attr_name, schema_key = constraint_mapping[constraint_type]
                if hasattr(constraint, attr_name):
                    schema[schema_key] = getattr(constraint, attr_name)
            elif constraint_type == "_PydanticGeneralMetadata" and hasattr(
                constraint, "pattern"
            ):
                schema["pattern"] = constraint.pattern

    def _apply_object_metadata(self, schema: dict, param_obj: Param) -> None:
        """Apply object-level metadata"""
        attrs = ["title", "description", "examples"]
        for attr in attrs:
            if hasattr(param_obj, attr):
                value = getattr(param_obj, attr)
                if value:
                    schema[attr] = value

    def _apply_default_value(self, schema: dict, param_obj: Param) -> None:
        """Apply default value if serializable"""
        if not (
            hasattr(param_obj, "default")
            and param_obj.default is not None
            and param_obj.default is not ...
            and not str(type(param_obj.default)).endswith("PydanticUndefinedType")
        ):
            return

        try:
            from pydantic_core import to_json

            to_json(param_obj.default)
            schema["default"] = param_obj.default
        except (TypeError, ValueError):
            pass

    def get_model_schema(self, model: type[BaseModel]) -> dict:
        """Get OpenAPI schema for a Pydantic model with thread-safe caching"""
        model_name = model.__name__
        cache_key = f"{model.__module__}.{model_name}"

        with self._cache_lock:
            if cache_key not in self._model_schema_cache:
                self._cache_model_schema(model, cache_key)

            if model_name not in self.definitions:
                self.definitions[model_name] = self._model_schema_cache[cache_key]

        return {"$ref": f"#/components/schemas/{model_name}"}

    def _cache_model_schema(self, model: type[BaseModel], cache_key: str) -> None:
        """Cache model schema and process nested definitions"""
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


class ParameterProcessor:
    """Helper class for processing route parameters"""

    def __init__(self, schema_builder: SchemaBuilder):
        self.schema_builder = schema_builder

    def process_route_parameters(self, route) -> tuple[list[dict], dict | None]:
        """Process route parameters and return parameters list and request body"""
        sig = inspect.signature(route.endpoint)
        path_params = self._extract_path_parameters(route.path)

        parameters = []
        request_body = None
        form_fields = {}
        multipart_fields = {}

        for param_name, param in sig.parameters.items():
            if self._should_skip_parameter(param):
                continue

            result = self._process_single_parameter(
                param_name, param, path_params, route.method
            )

            if result is None:
                continue

            param_type, data = result

            if param_type == "parameter":
                parameters.append(data)
            elif param_type == "parameters":  # Multiple parameters from model
                parameters.extend(data)
            elif param_type == "request_body":
                request_body = data
            elif param_type == "form":
                form_fields[param_name] = data
            elif param_type == "multipart":
                multipart_fields[param_name] = data

        # Build combined request body for form data
        if form_fields or multipart_fields:
            request_body = self._build_form_request_body(form_fields, multipart_fields)

        return parameters, request_body

    def _extract_path_parameters(self, path: str) -> set:
        """Extract path parameters from route path"""
        openapi_path = PATH_PARAM_PATTERN.sub(r"{\1}", path)
        return set(OPENAPI_PATH_PATTERN.findall(openapi_path))

    def _should_skip_parameter(self, param: inspect.Parameter) -> bool:
        """Determine if parameter should be skipped"""
        if isinstance(param.default, (Depends, Security)):
            return True

        # Skip authorization headers handled by security
        if isinstance(param.default, Header) and param.default.alias == "Authorization":
            return True

        return False

    def _process_single_parameter(
        self, param_name: str, param: inspect.Parameter, path_params: set, method: str
    ) -> tuple[str, Any] | None:
        """Process a single parameter and return its type and data"""

        # Handle Pydantic models
        if self._is_pydantic_model(param.annotation):
            return self._process_pydantic_model(param, method)

        # Handle file uploads
        if isinstance(param.default, File) or param.annotation == File:
            return "multipart", self._build_file_field_schema(param_name, param)

        # Handle form data
        if isinstance(param.default, Form):
            return "form", self._build_form_field_schema(param_name, param)

        # Handle body parameters
        if isinstance(param.default, Body):
            return "request_body", self._build_body_request_body(param)

        # Handle regular parameters
        param_info = self._build_parameter_info(param_name, param, path_params)
        if param_info:
            return "parameter", param_info

        return None

    def _process_pydantic_model(
        self, param: inspect.Parameter, method: str
    ) -> tuple[str, Any]:
        """Process Pydantic model parameter"""
        if method == "GET":
            # For GET, extract as query parameters
            query_params = self._build_query_params_from_model(param.annotation)
            return (
                "parameters",
                query_params,
            )  # Note: plural to indicate multiple parameters
        else:
            # For other methods, use as request body
            model_schema = self.schema_builder.get_model_schema(param.annotation)
            request_body = {
                "content": {"application/json": {"schema": model_schema}},
                "required": param.default is inspect.Parameter.empty,
            }
            return "request_body", request_body

    def _build_parameter_info(
        self, param_name: str, param: inspect.Parameter, path_params: set
    ) -> dict | None:
        """Build parameter info with full Param object integration"""
        param_obj = param.default

        if isinstance(param_obj, BaseParam) and not param_obj.include_in_schema:
            return None

        # Determine location and name
        location, actual_name = self._determine_parameter_location_and_name(
            param_name, param_obj, path_params
        )

        # Skip form data and body params - they're handled elsewhere
        if isinstance(param_obj, (Form, Body)):
            return None

        # Build schema
        schema = self._build_parameter_schema(param, param_obj)

        # Determine if required
        is_required = self._is_parameter_required(param_obj, param, location)

        param_info = {
            "name": actual_name,
            "in": location,
            "required": is_required,
            "schema": schema,
        }

        # Add additional metadata
        self._add_parameter_metadata(param_info, param_obj, actual_name)

        return param_info

    def _determine_parameter_location_and_name(
        self, param_name: str, param_obj: Any, path_params: set
    ) -> tuple[str, str]:
        """Determine parameter location and actual name"""
        if isinstance(param_obj, Param):
            location_mapping = {
                ParameterSource.QUERY: "query",
                ParameterSource.HEADER: "header",
                ParameterSource.COOKIE: "cookie",
                ParameterSource.PATH: "path",
            }
            location = location_mapping.get(param_obj.in_, "query")
            actual_name = param_obj.alias if param_obj.alias else param_name

            # Handle header name conversion
            if location == "header" and isinstance(param_obj, Header):
                if param_obj.convert_underscores and not param_obj.alias:
                    actual_name = param_name.replace("_", "-")
        elif param_name in path_params:
            location = "path"
            actual_name = param_name
        else:
            location = "query"
            actual_name = param_name

        return location, actual_name

    def _build_parameter_schema(self, param: inspect.Parameter, param_obj: Any) -> dict:
        """Build parameter schema"""
        if isinstance(param_obj, Param):
            result = self.schema_builder.build_parameter_schema_from_param(param)
            return result
        else:
            result = self.schema_builder.build_parameter_schema(param.annotation)
            return result

    def _is_parameter_required(
        self, param_obj: Any, param: inspect.Parameter, location: str
    ) -> bool:
        """Determine if parameter is required"""
        if isinstance(param_obj, BaseParam):
            return param_obj.default is ... or location == "path"
        else:
            return param.default is inspect.Parameter.empty or location == "path"

    def _add_parameter_metadata(
        self, param_info: dict, param_obj: Any, actual_name: str
    ) -> None:
        """Add metadata to parameter info"""
        # Add OpenAPI-specific fields from Param object
        if isinstance(param_obj, BaseParam):
            if param_obj.description:
                param_info["description"] = param_obj.description
            if hasattr(param_obj, "examples") and param_obj.examples:
                param_info["examples"] = {
                    f"example_{i}": {"value": example}
                    for i, example in enumerate(param_obj.examples)
                }
            if hasattr(param_obj, "deprecated") and param_obj.deprecated:
                param_info["deprecated"] = True

        # Add default descriptions for common parameters
        if "description" not in param_info:
            common_descriptions = {
                "page": "Pagination page",
                "limit": "Pagination limit",
                "offset": "Pagination offset",
                "sort": "Sorting sort",
                "order": "Sorting order",
                "sort_by": "Sorting sort_by",
            }
            if actual_name.lower() in common_descriptions:
                param_info["description"] = common_descriptions[actual_name.lower()]

    def _build_form_field_schema(
        self, param_name: str, param: inspect.Parameter
    ) -> dict:
        """Build schema for form field"""
        schema = self.schema_builder.build_parameter_schema_from_param(param)
        if "type" not in schema:
            schema["type"] = "string"
        return schema

    def _build_file_field_schema(
        self, param_name: str, param: inspect.Parameter
    ) -> dict:
        """Build schema for file field"""
        schema = {"type": "string", "format": "binary"}

        if isinstance(param.default, File) and param.default.description:
            schema["description"] = param.default.description

        return schema

    def _build_body_request_body(self, param: inspect.Parameter) -> dict:
        """Build request body for Body parameter"""
        param_obj = param.default
        content_type = getattr(param_obj, "media_type", "application/json")
        schema = self.schema_builder.build_parameter_schema_from_param(param)

        request_body = {
            "content": {content_type: {"schema": schema}},
            "required": param_obj.default is ...,
        }

        if param_obj.description:
            request_body["description"] = param_obj.description

        return request_body

    def _build_form_request_body(
        self, form_fields: dict, multipart_fields: dict
    ) -> dict | None:
        """Build request body for form/multipart data"""
        if multipart_fields:
            # Multipart form data
            all_fields = {**form_fields, **multipart_fields}
            return {
                "content": {
                    "multipart/form-data": {
                        "schema": {"type": "object", "properties": all_fields}
                    }
                }
            }
        elif form_fields:
            # URL-encoded form data
            return {
                "content": {
                    "application/x-www-form-urlencoded": {
                        "schema": {"type": "object", "properties": form_fields}
                    }
                }
            }
        return None

    def _build_query_params_from_model(
        self, model_class: type[BaseModel]
    ) -> list[dict]:
        """Convert Pydantic model fields to query parameters"""
        parameters = []
        model_schema = model_class.model_json_schema(mode="serialization")
        required_fields = model_schema.get("required", [])
        properties = model_schema.get("properties", {})

        for prop_name, prop_schema in properties.items():
            param_info = {
                "name": prop_name,
                "in": "query",
                "required": prop_name in required_fields,
                "schema": prop_schema,
            }

            # Add optional metadata
            for key in ["description", "examples"]:
                if key in prop_schema:
                    if key == "examples":
                        param_info[key] = {
                            f"example_{i}": {"value": example}
                            for i, example in enumerate(prop_schema[key])
                        }
                    else:
                        param_info[key] = prop_schema[key]

            parameters.append(param_info)

        return parameters

    @staticmethod
    def _is_pydantic_model(annotation) -> bool:
        """Check if annotation is a Pydantic model"""
        return isinstance(annotation, type) and issubclass(annotation, BaseModel)


class ResponseBuilder:
    """Helper class for building OpenAPI responses"""

    def __init__(self, schema_builder: SchemaBuilder):
        self.schema_builder = schema_builder

    def build_responses(self, route) -> dict:
        """Build responses section with enhanced error handling"""
        from http import HTTPStatus

        status_code = str(route.meta.get("status_code", 200))
        responses = {status_code: {"description": HTTPStatus(int(status_code)).phrase}}

        # Add response model if specified
        self._add_response_model(
            responses, status_code, route.meta.get("response_model")
        )

        # Add error responses
        self._add_security_error_responses(responses, route)
        self._add_custom_error_responses(responses, route)

        return responses

    def _add_response_model(
        self, responses: dict, status_code: str, response_model
    ) -> None:
        """Add response model to responses"""
        if not response_model:
            return

        origin = typing.get_origin(response_model)

        if origin is list:
            inner_type = typing.get_args(response_model)[0]
            if self._is_pydantic_model(inner_type):
                inner_schema = self.schema_builder.get_model_schema(inner_type)
                array_schema = {"type": "array", "items": inner_schema}
                responses[status_code]["content"] = {
                    "application/json": {"schema": array_schema}
                }
        elif self._is_pydantic_model(response_model):
            schema = self.schema_builder.get_model_schema(response_model)
            responses[status_code]["content"] = {"application/json": {"schema": schema}}

    def _add_security_error_responses(self, responses: dict, route) -> None:
        """Add security-related error responses"""
        if not route.meta.get("security"):
            return

        error_responses = {"401": "Unauthorized", "403": "Forbidden"}

        for code, description in error_responses.items():
            responses[code] = {
                "description": description,
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ErrorSchema"}
                    }
                },
            }

    def _add_custom_error_responses(self, responses: dict, route) -> None:
        """Add custom error responses"""
        from http import HTTPStatus

        custom_errors = route.meta.get("response_errors")
        if not custom_errors:
            return

        for error_code in custom_errors:
            responses[str(error_code)] = {
                "description": HTTPStatus(error_code).phrase,
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ErrorSchema"}
                    }
                },
            }

    @staticmethod
    def _is_pydantic_model(annotation) -> bool:
        """Check if annotation is a Pydantic model"""
        return isinstance(annotation, type) and issubclass(annotation, BaseModel)


class OpenAPIGenerator:
    """Generate OpenAPI schema from routes with full params.py integration"""

    def __init__(self, router):
        self.router = router
        self.definitions = {}
        self._cache_lock = threading.Lock()

        # Initialize helper classes
        self.schema_builder = SchemaBuilder(self.definitions, self._cache_lock)
        self.parameter_processor = ParameterProcessor(self.schema_builder)
        self.response_builder = ResponseBuilder(self.schema_builder)

    def generate(self) -> dict:
        """Generate complete OpenAPI schema"""
        self._add_error_schemas()
        paths = self._build_paths()

        schema = self._build_base_schema(paths)
        self._add_security_schemes(schema)
        self._add_global_security(schema)

        return schema

    def _build_paths(self) -> dict:
        """Build paths section from routes"""
        paths = {}

        for route in self.router.get_routes():
            openapi_path = self._convert_path(route.path)
            operation = self._build_operation(route)

            if openapi_path not in paths:
                paths[openapi_path] = {}

            paths[openapi_path][route.method.lower()] = operation

        return paths

    def _build_base_schema(self, paths: dict) -> dict:
        """Build base OpenAPI schema structure"""
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

    def _add_security_schemes(self, schema: dict) -> None:
        """Add security schemes if defined"""
        if hasattr(self.router, "_security_schemes") and self.router._security_schemes:
            schema["components"]["securitySchemes"] = self.router._security_schemes

    def _add_global_security(self, schema: dict) -> None:
        """Add global security if defined"""
        if hasattr(self.router, "_global_security") and self.router._global_security:
            schema["security"] = self.router._global_security

    @lru_cache(maxsize=128)
    def _convert_path(self, path: str) -> str:
        """Convert path format to OpenAPI format with caching"""
        return PATH_PARAM_PATTERN.sub(r"{\1}", path)

    def _has_security_dependency(self, route) -> bool:
        """Check if route has Security dependencies"""
        import inspect

        from fastopenapi.core.params import Security

        sig = inspect.signature(route.endpoint)
        for param in sig.parameters.values():
            if isinstance(param.default, Security):
                return True
        return False

    def _extract_security_scopes(self, route) -> list[str]:
        """Extract scopes from Security dependencies"""
        import inspect

        from fastopenapi.core.params import Security

        sig = inspect.signature(route.endpoint)
        all_scopes = []
        for param in sig.parameters.values():
            if isinstance(param.default, Security):
                all_scopes.extend(param.default.scopes)
        return list(set(all_scopes))  # Remove duplicates

    def _build_operation(self, route) -> dict:
        """Build operation object for a route"""
        parameters, request_body = self.parameter_processor.process_route_parameters(
            route
        )
        responses = self.response_builder.build_responses(route)

        operation = {
            "summary": route.endpoint.__doc__ or "",
            "responses": responses,
            "operationId": f"{route.method.lower()}_{route.endpoint.__name__}",
        }

        # Add optional fields
        self._add_optional_operation_fields(operation, route, parameters, request_body)

        # Auto-add security
        if (
            not operation.get("security")
            and self._has_security_dependency(route)
            and hasattr(self.router, "_security_schemes")
            and self.router._security_schemes
        ):
            scheme_name = list(self.router._security_schemes.keys())[0]
            scopes = self._extract_security_scopes(route)
            operation["security"] = [{scheme_name: scopes}]

        return operation

    def _add_optional_operation_fields(
        self, operation: dict, route, parameters: list[dict], request_body: dict | None
    ) -> None:
        """Add optional fields to operation"""
        if parameters:
            operation["parameters"] = parameters
        if request_body:
            operation["requestBody"] = request_body
        if route.meta.get("tags"):
            operation["tags"] = route.meta["tags"]
        if route.meta.get("deprecated"):
            operation["deprecated"] = True
        if route.meta.get("security"):
            operation["security"] = route.meta["security"]
        if route.meta.get("description"):
            operation["description"] = route.meta["description"]

    def _add_error_schemas(self):
        """Add comprehensive error response schemas"""
        self.definitions.update(
            {
                "ErrorSchema": self._build_error_schema(),
                "PaginationParams": self._build_pagination_params_schema(),
            }
        )

    def _build_error_schema(self) -> dict:
        """Build general error schema"""
        return {
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

    def _build_pagination_params_schema(self) -> dict:
        """Build pagination parameters schema"""
        return {
            "type": "object",
            "properties": {
                "page": {
                    "type": "integer",
                    "minimum": 1,
                    "default": 1,
                    "description": "Page number",
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 20,
                    "description": "Items per page",
                },
            },
        }
