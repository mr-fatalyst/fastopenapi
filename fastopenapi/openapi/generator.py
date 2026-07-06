import inspect
import re
import threading
import types
import typing
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from pydantic import BaseModel
from pydantic_core import PydanticUndefined

from fastopenapi.core.constants import (
    NO_BODY_METHODS,
    PYTHON_TYPE_MAPPING,
    ParameterSource,
)
from fastopenapi.core.params import (
    BaseParam,
    Body,
    Depends,
    File,
    Form,
    Header,
    Param,
    Security,
    is_body_model_annotation,
    is_pydantic_model,
    unwrap_annotated_parameter,
)
from fastopenapi.core.router import BaseRouter, RouteInfo

# Thread-safe compiled regex patterns
PATH_PARAM_PATTERN = re.compile(r"<(?:[^:>]+:)?([^>]+)>")
OPENAPI_PATH_PATTERN = re.compile(r"{(\w+)}")


@lru_cache(maxsize=256)
def _convert_path_to_openapi(path: str) -> str:
    """Convert framework path format to OpenAPI format.

    Module-level so lru_cache does not key on (and retain) generator
    instances.
    """
    return PATH_PARAM_PATTERN.sub(r"{\1}", path)


@dataclass
class ParameterInfo:
    """Data class for parameter information"""

    name: str
    location: str
    schema: dict[str, Any]
    required: bool = False
    description: str | None = None
    examples: dict[str, Any] | None = None
    deprecated: bool = False


class SchemaBuilder:
    """Helper class for building OpenAPI schemas"""

    def __init__(
        self,
        definitions: dict[str, Any],
        cache_lock: threading.Lock,
        openapi_version: str = "3.0.0",
    ):
        self.definitions = definitions
        self._cache_lock = cache_lock
        self._model_schema_cache: dict[str, Any] = {}
        # cache_key -> schema name assigned in components (collision-safe)
        self._schema_names: dict[str, str] = {}
        self._openapi_31 = openapi_version.startswith("3.1")

    def build_parameter_schema(self, annotation: Any) -> dict[str, Any]:
        """Build OpenAPI schema for a parameter annotation"""
        if hasattr(annotation, "__metadata__"):
            annotation = annotation.__origin__

        if self._is_pydantic_model(annotation):
            return self.get_model_schema(annotation)

        origin = typing.get_origin(annotation)

        if origin is list:
            return self._build_array_schema(annotation)

        if origin is typing.Union or (
            hasattr(types, "UnionType") and origin is types.UnionType
        ):
            return self._build_union_schema(annotation)

        return {"type": PYTHON_TYPE_MAPPING.get(annotation, "string")}

    def _build_array_schema(self, annotation: Any) -> dict[str, Any]:
        """Build schema for array types"""
        args = typing.get_args(annotation)
        items = self.build_parameter_schema(args[0]) if args else {"type": "string"}
        return {"type": "array", "items": items}

    def _build_union_schema(self, annotation: Any) -> dict[str, Any]:
        """Build schema for Union types (including Optional)"""
        args = typing.get_args(annotation)
        non_none_args = [arg for arg in args if arg is not type(None)]
        nullable = type(None) in args

        if not non_none_args:
            return {"type": "null"} if self._openapi_31 else {"type": "string"}

        if len(non_none_args) == 1:
            schema = self.build_parameter_schema(non_none_args[0])
        else:
            schema = {
                "anyOf": [self.build_parameter_schema(arg) for arg in non_none_args]
            }

        return self.make_nullable(schema) if nullable else schema

    def make_nullable(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Mark a schema as nullable per the target OpenAPI version.

        3.1 is JSON Schema ('null' type / anyOf); 3.0.x uses the
        'nullable' keyword, which must not sit next to a bare $ref.
        """
        if self._openapi_31:
            if isinstance(schema.get("type"), str):
                return {**schema, "type": [schema["type"], "null"]}
            return {"anyOf": [schema, {"type": "null"}]}
        if "$ref" in schema:
            return {"allOf": [schema], "nullable": True}
        return {**schema, "nullable": True}

    def build_parameter_schema_from_param(
        self, param: inspect.Parameter
    ) -> dict[str, Any]:
        """Build OpenAPI schema from Param object with full constraint support"""
        param_obj = param.default
        annotation = (
            param.annotation if param.annotation != inspect.Parameter.empty else str
        )

        schema = self.build_parameter_schema(annotation)

        if isinstance(param_obj, BaseParam):
            self._apply_param_constraints(schema, param_obj)

        return schema

    def _apply_param_constraints(
        self, schema: dict[str, Any], param_obj: BaseParam
    ) -> None:
        """Apply validation constraints from Param object to schema"""
        self._apply_metadata_constraints(schema, param_obj)
        self._apply_object_metadata(schema, param_obj)
        self._apply_default_value(schema, param_obj)

    def _apply_metadata_constraints(
        self, schema: dict[str, Any], param_obj: BaseParam
    ) -> None:
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
                if hasattr(constraint, attr_name):  # pragma: no cover
                    schema[schema_key] = getattr(constraint, attr_name)
            elif (  # pragma: no cover
                constraint_type == "_PydanticGeneralMetadata"
                and hasattr(constraint, "pattern")
            ):
                schema["pattern"] = constraint.pattern

    def _apply_object_metadata(
        self, schema: dict[str, Any], param_obj: BaseParam
    ) -> None:
        """Apply object-level metadata"""
        attrs = ["title", "description", "example", "examples"]
        for attr in attrs:
            if hasattr(param_obj, attr):  # pragma: no cover
                value = getattr(param_obj, attr)
                if value:
                    schema[attr] = value

    def _apply_default_value(
        self, schema: dict[str, Any], param_obj: BaseParam
    ) -> None:
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

    @staticmethod
    def _is_pydantic_model(annotation: Any) -> bool:
        return is_pydantic_model(annotation)

    def get_model_schema(self, model: type[BaseModel]) -> dict[str, Any]:
        """Get OpenAPI schema for a Pydantic model with thread-safe caching.

        Distinct models sharing a __name__ get suffixed schema names
        (User, User2, ...) instead of silently reusing the first schema.
        """
        cache_key = f"{model.__module__}.{model.__qualname__}"

        with self._cache_lock:
            schema_name = self._schema_names.get(cache_key)
            if schema_name is None:
                schema_name = self._assign_schema_name(model)
                self._schema_names[cache_key] = schema_name
                if cache_key not in self._model_schema_cache:
                    self._cache_model_schema(model, cache_key)
                self.definitions[schema_name] = self._model_schema_cache[cache_key]

        return {"$ref": f"#/components/schemas/{schema_name}"}

    def _assign_schema_name(self, model: type[BaseModel]) -> str:
        """Pick a components/schemas name that is not taken by another model"""
        base = model.__name__
        name = base
        counter = 2
        taken = set(self.definitions) | set(self._schema_names.values())
        while name in taken:
            name = f"{base}{counter}"
            counter += 1
        return name

    def build_inline_model_schema(self, model: type[BaseModel]) -> dict[str, Any]:
        """Model schema for inline use (query params from a model):
        nested $defs are moved into components so their $refs stay valid,
        but the model itself is not registered as a component."""
        schema = model.model_json_schema(
            mode="serialization",
            ref_template="#/components/schemas/{model}",
        )
        with self._cache_lock:
            self._extract_nested_definitions(schema)
        return schema

    def _cache_model_schema(self, model: type[BaseModel], cache_key: str) -> None:
        """Cache model schema and process nested definitions"""
        model_schema = model.model_json_schema(
            mode="serialization",
            ref_template="#/components/schemas/{model}",
        )
        self._extract_nested_definitions(model_schema)
        self._model_schema_cache[cache_key] = model_schema

    def _extract_nested_definitions(self, model_schema: dict[str, Any]) -> None:
        """Move nested $defs into components without clobbering existing ones"""
        for key in ("definitions", "$defs"):
            if key in model_schema:
                for name, sub_schema in model_schema[key].items():
                    self.definitions.setdefault(name, sub_schema)
                del model_schema[key]


class ParameterProcessor:
    """Helper class for processing route parameters"""

    def __init__(self, schema_builder: SchemaBuilder):
        self.schema_builder = schema_builder

    def process_route_parameters(
        self, route: RouteInfo
    ) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
        """Process route parameters and return parameters list and request body"""
        sig = inspect.signature(route.endpoint)
        path_params = self._extract_path_parameters(route.path)

        parameters: list[dict[str, Any]] = []
        body_fields: dict[str, dict[str, Any]] = {}
        form_fields: dict[str, Any] = {}
        multipart_fields: dict[str, Any] = {}
        form_required: list[str] = []
        has_explicit_embed = False

        for param_name, param in sig.parameters.items():
            param = unwrap_annotated_parameter(param)
            if self._should_skip_parameter(param):
                continue

            result = self._process_single_parameter(
                param_name, param, path_params, route.method
            )

            if result is None:
                continue

            self._classify_parameter_result(
                result,
                param_name,
                param,
                parameters,
                body_fields,
                form_fields,
                multipart_fields,
                form_required,
            )
            if isinstance(param.default, Body) and param.default.embed:
                has_explicit_embed = True

        request_body = self._resolve_request_body(
            body_fields,
            form_fields,
            multipart_fields,
            has_explicit_embed,
            form_required,
        )
        return parameters, request_body

    def _classify_parameter_result(
        self,
        result: tuple[str, Any],
        param_name: str,
        param: inspect.Parameter,
        parameters: list[dict[str, Any]],
        body_fields: dict[str, Any],
        form_fields: dict[str, Any],
        multipart_fields: dict[str, Any],
        form_required: list[str],
    ) -> None:
        """Classify a processed parameter result into the appropriate collection"""
        param_type, data = result

        if param_type == "parameter":
            parameters.append(data)
        elif param_type == "parameters":
            parameters.extend(data)
        elif param_type == "request_body":
            body_fields[param_name] = data
        elif param_type == "form":
            form_fields[param_name] = data
            if self._is_form_field_required(param):
                form_required.append(param_name)
        elif param_type == "multipart":  # pragma: no cover
            multipart_fields[param_name] = data
            if self._is_form_field_required(param):
                form_required.append(param_name)

    def _resolve_request_body(
        self,
        body_fields: dict[str, dict[str, Any]],
        form_fields: dict[str, Any],
        multipart_fields: dict[str, Any],
        has_explicit_embed: bool,
        form_required: list[str] | None = None,
    ) -> dict[str, Any] | None:
        """Resolve final request body from collected fields"""
        if form_fields or multipart_fields:
            return self._build_form_request_body(
                form_fields, multipart_fields, form_required or []
            )
        if len(body_fields) > 1 or has_explicit_embed:
            return self._build_embedded_request_body(body_fields)
        if body_fields:
            return next(iter(body_fields.values()))
        return None

    def _extract_path_parameters(self, path: str) -> set[str]:
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
        self,
        param_name: str,
        param: inspect.Parameter,
        path_params: set[str],
        method: str,
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

        # Handle containers of models (list[Model], Model | None, ...)
        if (
            self._is_body_model_annotation(param.annotation)
            and method not in NO_BODY_METHODS
        ):
            return "request_body", self._build_model_container_body(param)

        # Handle regular parameters
        param_info = self._build_parameter_info(param_name, param, path_params)
        if param_info:
            return "parameter", param_info

        return None

    def _process_pydantic_model(
        self, param: inspect.Parameter, method: str
    ) -> tuple[str, Any]:
        """Process Pydantic model parameter"""
        if method in NO_BODY_METHODS:
            # For no-body methods, extract as query parameters
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

    @staticmethod
    def _is_body_model_annotation(annotation: Any) -> bool:
        """Check if annotation is a model or a container of models"""
        return is_body_model_annotation(annotation)

    def _build_model_container_body(self, param: inspect.Parameter) -> dict[str, Any]:
        """Build request body for containers of models"""
        return {
            "content": {
                "application/json": {
                    "schema": self._model_container_schema(param.annotation)
                }
            },
            "required": param.default is inspect.Parameter.empty,
        }

    def _model_container_schema(self, annotation: Any) -> dict[str, Any]:
        """Build schema for a model or a container of models"""
        if self._is_pydantic_model(annotation):
            return self.schema_builder.get_model_schema(annotation)
        origin = typing.get_origin(annotation)
        args = typing.get_args(annotation)
        if origin is list and args:
            return {"type": "array", "items": self._model_container_schema(args[0])}
        if origin is typing.Union or origin is types.UnionType:
            non_none = [arg for arg in args if arg is not type(None)]
            # typing normalizes away all-None unions, and the body-model
            # guard guarantees at least one model member
            if non_none:  # pragma: no branch
                if len(non_none) == 1:
                    schema = self._model_container_schema(non_none[0])
                else:
                    schema = {
                        "anyOf": [self._model_container_schema(a) for a in non_none]
                    }
                if type(None) in args:
                    schema = self.schema_builder.make_nullable(schema)
                return schema
        return self.schema_builder.build_parameter_schema(annotation)

    def _build_parameter_info(
        self, param_name: str, param: inspect.Parameter, path_params: set[str]
    ) -> dict[str, Any] | None:
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
        self, param_name: str, param_obj: Any, path_params: set[str]
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

    def _build_parameter_schema(
        self, param: inspect.Parameter, param_obj: Any
    ) -> dict[str, Any]:
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
            is_undefined = (
                param_obj.default is ... or param_obj.default is PydanticUndefined
            )
            return is_undefined or location == "path"
        else:
            return param.default is inspect.Parameter.empty or location == "path"

    def _add_parameter_metadata(
        self, param_info: dict[str, Any], param_obj: Any, actual_name: str
    ) -> None:
        """Add metadata to parameter info"""
        # Add OpenAPI-specific fields from Param object
        if isinstance(param_obj, BaseParam):
            if param_obj.description:
                param_info["description"] = param_obj.description
            if hasattr(param_obj, "example") and param_obj.example is not None:
                param_info["example"] = param_obj.example
            if hasattr(param_obj, "examples") and param_obj.examples:
                param_info["examples"] = {
                    f"example_{i}": {"value": example}
                    for i, example in enumerate(param_obj.examples)
                }
            if hasattr(param_obj, "deprecated") and param_obj.deprecated:
                param_info["deprecated"] = True

    def _build_form_field_schema(
        self, param_name: str, param: inspect.Parameter
    ) -> dict[str, Any]:
        """Build schema for form field"""
        schema = self.schema_builder.build_parameter_schema_from_param(param)
        if "type" not in schema:
            schema["type"] = "string"
        return schema

    def _build_file_field_schema(
        self, param_name: str, param: inspect.Parameter
    ) -> dict[str, Any]:
        """Build schema for file field"""
        schema = {"type": "string", "format": "binary"}

        if isinstance(param.default, File) and param.default.description:
            schema["description"] = param.default.description

        return schema

    def _build_body_request_body(self, param: inspect.Parameter) -> dict[str, Any]:
        """Build request body for Body parameter"""
        param_obj = param.default
        content_type = getattr(param_obj, "media_type", "application/json")
        schema = self.schema_builder.build_parameter_schema_from_param(param)

        request_body = {
            "content": {content_type: {"schema": schema}},
            "required": param_obj.default is ...
            or param_obj.default is PydanticUndefined,
        }

        if param_obj.description:
            request_body["description"] = param_obj.description

        return request_body

    @staticmethod
    def _build_embedded_request_body(
        body_fields: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """Build request body with multiple body params embedded by name"""
        properties = {}
        required = []
        content_type = "application/json"
        for name, field_body in body_fields.items():
            content = field_body.get("content", {})
            ct = next(iter(content), "application/json")
            schema = content.get(ct, {}).get("schema", {})
            properties[name] = schema
            if field_body.get("required", False):
                required.append(name)
            if len(body_fields) == 1:
                content_type = ct

        wrapper_schema: dict[str, Any] = {
            "type": "object",
            "properties": properties,
        }
        if required:
            wrapper_schema["required"] = required

        return {
            "content": {content_type: {"schema": wrapper_schema}},
            "required": True,
        }

    def _build_form_request_body(
        self,
        form_fields: dict[str, Any],
        multipart_fields: dict[str, Any],
        required: list[str] | None = None,
    ) -> dict[str, Any] | None:
        """Build request body for form/multipart data"""
        if multipart_fields:
            all_fields = {**form_fields, **multipart_fields}
            schema: dict[str, Any] = {
                "type": "object",
                "properties": all_fields,
            }
            if required:
                schema["required"] = required
            return {"content": {"multipart/form-data": {"schema": schema}}}
        elif form_fields:
            schema = {
                "type": "object",
                "properties": form_fields,
            }
            if required:
                schema["required"] = required
            return {
                "content": {"application/x-www-form-urlencoded": {"schema": schema}}
            }
        return None

    @staticmethod
    def _is_form_field_required(param: inspect.Parameter) -> bool:
        """Check if a Form/File parameter is required"""
        if isinstance(param.default, BaseParam):
            return (
                param.default.default is ...
                or param.default.default is PydanticUndefined
            )
        return param.default is inspect.Parameter.empty

    def _build_query_params_from_model(
        self, model_class: type[BaseModel]
    ) -> list[dict[str, Any]]:
        """Convert Pydantic model fields to query parameters"""
        parameters = []
        # Inline schema: nested $defs land in components so $refs in
        # field schemas stay resolvable
        model_schema = self.schema_builder.build_inline_model_schema(model_class)
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
    def _is_pydantic_model(annotation: Any) -> bool:
        """Check if annotation is a Pydantic model"""
        return isinstance(annotation, type) and issubclass(annotation, BaseModel)


class ResponseSectionBuilder:
    """Build the OpenAPI responses section of an operation.

    Not to be confused with fastopenapi.response.builder.ResponseBuilder,
    which serializes runtime responses.
    """

    def __init__(self, schema_builder: SchemaBuilder):
        self.schema_builder = schema_builder

    def build_responses(
        self, route: RouteInfo, has_security: bool = False
    ) -> dict[str, Any]:
        """Build responses section with enhanced error handling"""
        from http import HTTPStatus

        status_code = str(route.meta.get("status_code", 200))
        responses = {status_code: {"description": HTTPStatus(int(status_code)).phrase}}

        # Add response model if specified
        self._add_response_model(
            responses, status_code, route.meta.get("response_model")
        )

        # Add error responses
        self._add_security_error_responses(responses, route, has_security)
        self._add_custom_error_responses(responses, route)

        return responses

    def _add_response_model(
        self, responses: dict[str, Any], status_code: str, response_model: Any
    ) -> None:
        """Add response model to responses"""
        if not response_model:
            return

        origin = typing.get_origin(response_model)

        if origin is list:
            inner_type = typing.get_args(response_model)[0]
            if self._is_pydantic_model(inner_type):
                inner_schema = self.schema_builder.get_model_schema(inner_type)
                schema = {"type": "array", "items": inner_schema}
            else:
                schema = self.schema_builder.build_parameter_schema(response_model)
        elif self._is_pydantic_model(response_model):
            schema = self.schema_builder.get_model_schema(response_model)
        else:
            schema = self.schema_builder.build_parameter_schema(response_model)

        responses[status_code]["content"] = {"application/json": {"schema": schema}}

    def _add_security_error_responses(
        self, responses: dict[str, Any], route: RouteInfo, has_security: bool = False
    ) -> None:
        """Add security-related error responses"""
        if not has_security:
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

    def _add_custom_error_responses(
        self, responses: dict[str, Any], route: RouteInfo
    ) -> None:
        """Add custom error responses"""
        from http import HTTPStatus

        custom_errors = route.meta.get("response_errors")
        custom_responses = route.meta.get("responses")

        if custom_errors:
            for error_code in custom_errors:
                responses[str(error_code)] = {
                    "description": HTTPStatus(error_code).phrase,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ErrorSchema"}
                        }
                    },
                }

        if custom_responses:
            for status_code, response_info in custom_responses.items():
                str_code = str(status_code)
                model = None
                if isinstance(response_info, dict):
                    description = response_info.get(
                        "description", HTTPStatus(int(status_code)).phrase
                    )
                    model = response_info.get("model")
                    schema = (
                        self.schema_builder.get_model_schema(model)
                        if model and self._is_pydantic_model(model)
                        else {"$ref": "#/components/schemas/ErrorSchema"}
                    )
                else:
                    description = HTTPStatus(int(status_code)).phrase
                    schema = {"$ref": "#/components/schemas/ErrorSchema"}

                if str_code in responses:
                    responses[str_code]["description"] = description
                    if model and self._is_pydantic_model(model):
                        responses[str_code]["content"] = {
                            "application/json": {"schema": schema}
                        }
                else:
                    responses[str_code] = {
                        "description": description,
                        "content": {"application/json": {"schema": schema}},
                    }

    @staticmethod
    def _is_pydantic_model(annotation: Any) -> bool:
        """Check if annotation is a Pydantic model"""
        return isinstance(annotation, type) and issubclass(annotation, BaseModel)


class OpenAPIGenerator:
    """Generate OpenAPI schema from routes with full params.py integration"""

    def __init__(self, router: BaseRouter):
        self.router = router
        self.definitions: dict[str, Any] = {}
        self._cache_lock = threading.Lock()
        self._operation_ids: set[str] = set()

        # Initialize helper classes
        self.schema_builder = SchemaBuilder(
            self.definitions, self._cache_lock, router.openapi_version
        )
        self.parameter_processor = ParameterProcessor(self.schema_builder)
        self.response_builder = ResponseSectionBuilder(self.schema_builder)

    def generate(self) -> dict[str, Any]:
        """Generate complete OpenAPI schema"""
        self._add_error_schemas()
        paths = self._build_paths()

        schema = self._build_base_schema(paths)
        self._add_security_schemes(schema)
        self._add_global_security(schema)

        return schema

    def _build_paths(self) -> dict[str, Any]:
        """Build paths section from routes"""
        paths: dict[str, Any] = {}

        for route in self.router.get_routes():
            openapi_path = self._convert_path(route.path)
            operation = self._build_operation(route)

            if openapi_path not in paths:
                paths[openapi_path] = {}

            paths[openapi_path][route.method.lower()] = operation

        return paths

    def _build_base_schema(self, paths: dict[str, Any]) -> dict[str, Any]:
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

    def _add_security_schemes(self, schema: dict[str, Any]) -> None:
        """Add security schemes if defined"""
        if hasattr(self.router, "_security_schemes") and self.router._security_schemes:
            schema["components"]["securitySchemes"] = self.router._security_schemes

    def _add_global_security(self, schema: dict[str, Any]) -> None:
        """Add global security if defined"""
        if hasattr(self.router, "_global_security") and self.router._global_security:
            schema["security"] = self.router._global_security

    def _build_operation_id(self, route: RouteInfo) -> str:
        """Build a unique operationId (spec requires uniqueness).

        Explicit operation_id is used verbatim; autogenerated ones get a
        numeric suffix when two handlers share a method and function name.
        """
        explicit: str | None = route.meta.get("operation_id")
        if explicit:
            self._operation_ids.add(explicit)
            return explicit

        base = f"{route.method.lower()}_{route.endpoint.__name__}"
        operation_id = base
        counter = 2
        while operation_id in self._operation_ids:
            operation_id = f"{base}_{counter}"
            counter += 1
        self._operation_ids.add(operation_id)
        return operation_id

    def _convert_path(self, path: str) -> str:
        """Convert path format to OpenAPI format with caching"""
        return _convert_path_to_openapi(path)

    def _has_security_dependency(self, route: RouteInfo) -> bool:
        """Check if route has Security dependencies"""
        sig = inspect.signature(route.endpoint)
        for param in sig.parameters.values():
            if isinstance(unwrap_annotated_parameter(param).default, Security):
                return True
        return False

    def _extract_security_scopes(self, route: RouteInfo) -> list[str]:
        """Extract scopes from Security dependencies"""
        sig = inspect.signature(route.endpoint)
        all_scopes = []
        for param in sig.parameters.values():
            default = unwrap_annotated_parameter(param).default
            if isinstance(default, Security):
                all_scopes.extend(default.scopes)
        return list(set(all_scopes))  # Remove duplicates

    def _build_operation(self, route: RouteInfo) -> dict[str, Any]:
        """Build operation object for a route"""
        parameters, request_body = self.parameter_processor.process_route_parameters(
            route
        )
        has_security = bool(
            route.meta.get("security")
        ) or self._has_security_dependency(route)
        responses = self.response_builder.build_responses(route, has_security)

        operation = {
            "summary": route.meta.get("summary")
            or route.endpoint.__name__.replace("_", " ").title(),
            "responses": responses,
            "operationId": self._build_operation_id(route),
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
        self,
        operation: dict[str, Any],
        route: RouteInfo,
        parameters: list[dict[str, Any]],
        request_body: dict[str, Any] | None,
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
        description = route.meta.get("description") or route.endpoint.__doc__
        if description:
            operation["description"] = description

    def _add_error_schemas(self) -> None:
        """Add the error envelope schema referenced by error responses"""
        self.definitions["ErrorSchema"] = self._build_error_schema()

    def _build_error_schema(self) -> dict[str, Any]:
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
