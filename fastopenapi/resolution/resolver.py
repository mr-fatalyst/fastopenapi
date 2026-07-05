import inspect
import types
import typing
from collections.abc import Callable, Mapping
from types import MappingProxyType
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter
from pydantic import ValidationError as PydanticValidationError
from pydantic import create_model
from pydantic_core import PydanticUndefined

from fastopenapi.core.constants import NO_BODY_METHODS, ParameterSource
from fastopenapi.core.dependency_resolver import dependency_resolver
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
from fastopenapi.core.types import RequestData
from fastopenapi.errors.exceptions import ValidationError


class ProcessedParameter:
    """Container for processed parameter information"""

    def __init__(
        self,
        value: Any,
        needs_validation: bool = False,
        field_info: tuple[Any, ...] | None = None,
    ):
        self.value = value
        self.needs_validation = needs_validation
        self.field_info = field_info


class ParameterResolver:
    """Resolve and validate endpoint parameters"""

    # Cache for dynamic models
    _param_model_cache: dict[frozenset[tuple[str, ...]], type[BaseModel]] = {}
    # Cache endpoint signature
    _signature_cache: dict[
        Callable[..., Any], MappingProxyType[str, inspect.Parameter]
    ] = {}
    # Cache for TypeAdapter instances (keyed by annotation)
    _type_adapter_cache: dict[Any, TypeAdapter[Any]] = {}

    @classmethod
    def _get_signature(
        cls, endpoint: Callable[..., Any]
    ) -> MappingProxyType[str, inspect.Parameter]:
        """Get cached signature parameters for endpoint"""
        if endpoint not in cls._signature_cache:
            sig = inspect.signature(endpoint)
            params = {
                name: unwrap_annotated_parameter(param)
                for name, param in sig.parameters.items()
            }
            cls._signature_cache[endpoint] = MappingProxyType(params)
        return cls._signature_cache[endpoint]

    @classmethod
    def _get_type_adapter(cls, annotation: Any) -> TypeAdapter[Any]:
        """Get cached TypeAdapter for annotation"""
        adapter = cls._type_adapter_cache.get(annotation)
        if adapter is None:
            adapter = cls._type_adapter_cache.setdefault(
                annotation, TypeAdapter(annotation)
            )
        return adapter

    @classmethod
    def resolve(
        cls, endpoint: Callable[..., Any], request_data: RequestData
    ) -> dict[str, Any]:
        """Resolve all parameters for an endpoint"""
        params = cls._get_signature(endpoint)
        method = getattr(endpoint, "__route_meta__", {}).get("method")
        kwargs = {}

        # Resolve dependencies first
        kwargs.update(cls._resolve_dependencies(endpoint, request_data))

        # Process regular parameters
        regular_kwargs, model_fields, model_values = cls._process_parameters(
            params, request_data, method=method
        )
        kwargs.update(regular_kwargs)

        # Validate collected parameters
        if model_fields:
            validated_params = cls._validate_parameters(
                endpoint, model_fields, model_values
            )
            kwargs.update(validated_params)

        return kwargs

    @classmethod
    async def resolve_async(
        cls, endpoint: Callable[..., Any], request_data: RequestData
    ) -> dict[str, Any]:
        params = cls._get_signature(endpoint)
        method = getattr(endpoint, "__route_meta__", {}).get("method")
        kwargs = {}

        # Async dependencies
        kwargs.update(await cls._resolve_dependencies_async(endpoint, request_data))

        # Sync parameters
        regular_kwargs, model_fields, model_values = cls._process_parameters(
            params, request_data, method=method
        )
        kwargs.update(regular_kwargs)

        if model_fields:
            kwargs.update(
                cls._validate_parameters(endpoint, model_fields, model_values)
            )

        return kwargs

    @classmethod
    def resolve_params(
        cls,
        params: Mapping[str, inspect.Parameter],
        request_data: RequestData,
        *,
        method: str | None = None,
        owner: tuple[str, str] = ("fastopenapi", "<params>"),
    ) -> dict[str, Any]:
        """Resolve a bare parameter mapping (e.g. dependency sub-parameters).

        ``owner`` identifies the callable the params belong to and keys the
        validation-model cache.
        """
        regular_kwargs, model_fields, model_values = cls._process_parameters(
            params, request_data, method=method
        )
        kwargs = dict(regular_kwargs)
        if model_fields:
            kwargs.update(cls._validate_fields(owner, model_fields, model_values))
        return kwargs

    @staticmethod
    def _resolve_dependencies(
        endpoint: Callable[..., Any], request_data: RequestData
    ) -> dict[str, Any]:
        """Resolve endpoint dependencies"""
        return dependency_resolver.resolve_dependencies(endpoint, request_data)

    @staticmethod
    async def _resolve_dependencies_async(
        endpoint: Callable[..., Any], request_data: RequestData
    ) -> dict[str, Any]:
        """Resolve endpoint dependencies"""
        return await dependency_resolver.resolve_dependencies_async(
            endpoint, request_data
        )

    @classmethod
    def _should_embed_body(
        cls,
        params: MappingProxyType[str, inspect.Parameter],
        path_params: dict[str, Any],
        method: str | None = None,
    ) -> bool:
        """Determine if body parameters should be embedded (keyed by param name)"""
        body_params = []
        has_explicit_embed = False
        for name, param in params.items():
            if isinstance(param.default, (Depends, Security)):
                continue
            source = cls._determine_source(name, param, path_params, method)
            if source == ParameterSource.BODY:
                body_params.append(name)
                if isinstance(param.default, Body) and param.default.embed:
                    has_explicit_embed = True
        return len(body_params) > 1 or has_explicit_embed

    @classmethod
    def _process_parameters(
        cls,
        params: Mapping[str, inspect.Parameter],
        request_data: RequestData,
        method: str | None = None,
    ) -> tuple[dict[str, Any], dict[str, tuple[Any, ...] | None], dict[str, Any]]:
        """Process all endpoint parameters"""
        regular_kwargs = {}
        model_fields = {}
        model_values = {}

        embed = cls._should_embed_body(params, request_data.path_params, method)

        for name, param in params.items():
            # Skip dependency parameters - already resolved
            if isinstance(param.default, (Depends, Security)):
                continue

            # Handle models and containers of models (validated as a whole)
            if not isinstance(param.default, BaseParam) and (
                cls._is_body_model_annotation(param.annotation)
            ):
                source = cls._determine_source(
                    name, param, request_data.path_params, method
                )
                if source == ParameterSource.BODY:
                    regular_kwargs[name] = cls._resolve_body_value(
                        name, param, request_data, embed
                    )
                    continue
                if cls._is_pydantic_model(param.annotation):
                    # No-body methods map model fields onto query params
                    regular_kwargs[name] = cls._resolve_pydantic_model(
                        param.annotation, request_data.query_params, name
                    )
                    continue
                # model containers on no-body methods fall through

            processed_param = cls._process_single_parameter(
                name, param, request_data, embed, method
            )

            if processed_param.needs_validation:
                model_fields[name] = processed_param.field_info
                model_values[name] = processed_param.value
            else:
                regular_kwargs[name] = processed_param.value

        return regular_kwargs, model_fields, model_values

    @classmethod
    def _resolve_body_value(
        cls,
        name: str,
        param: inspect.Parameter,
        request_data: RequestData,
        embed: bool,
    ) -> Any:
        """Resolve a model (or container of models) from the request body"""
        body = request_data.body
        if embed:
            data = (body or {}).get(cls._get_param_name(name, param))
        else:
            data = body

        if (data is None or data == {}) and not cls._is_required_param(param):
            return cls._get_default_value(param)

        if cls._is_pydantic_model(param.annotation):
            return cls._resolve_pydantic_model(param.annotation, data or {}, name)

        adapter = cls._get_type_adapter(param.annotation)
        try:
            return adapter.validate_python(data)
        except PydanticValidationError as e:
            raise ValidationError(f"Validation error for parameter '{name}'", str(e))

    @classmethod
    def _process_single_parameter(
        cls,
        name: str,
        param: inspect.Parameter,
        request_data: RequestData,
        embed: bool = False,
        method: str | None = None,
    ) -> ProcessedParameter:
        """Process a single parameter"""
        source = cls._determine_source(name, param, request_data.path_params, method)

        # Handle Pydantic models
        if cls._is_pydantic_model(param.annotation):
            if source == ParameterSource.BODY:
                body = request_data.body or {}
                data = body.get(name, {}) if embed else body
            else:
                data = request_data.query_params
            resolved_model = cls._resolve_pydantic_model(param.annotation, data, name)
            return ProcessedParameter(value=resolved_model, needs_validation=False)

        # Extract value based on source
        if embed and source == ParameterSource.BODY:
            body = request_data.body or {}
            value = body.get(name)
        else:
            value = cls._extract_value(name, param, source, request_data)

        # Multi-value sources deliver a scalar when only one value was sent;
        # list-typed params still expect a one-item list
        if value is not None and source in (
            ParameterSource.QUERY,
            ParameterSource.FORM,
        ):
            value = cls._coerce_scalar_to_list(value, param.annotation)

        # Handle missing required parameters
        if value is None and cls._is_required_param(param):
            param_name = cls._get_param_name(name, param)
            raise ValidationError(f"Missing required parameter: '{param_name}'")
        elif value is None:
            value = cls._get_default_value(param)

        # Determine if validation is needed
        needs_validation = value is not None and cls._needs_validation(param)

        field_info = None
        if needs_validation:
            if isinstance(param.default, BaseParam):
                field_info = cls._build_field_info(param)
            else:
                annotation = (
                    param.annotation
                    if param.annotation != inspect.Parameter.empty
                    else Any
                )
                field_info = (annotation, ...)

        return ProcessedParameter(
            value=value, needs_validation=needs_validation, field_info=field_info
        )

    @staticmethod
    def _determine_source(
        name: str,
        param: inspect.Parameter,
        path_params: dict[str, Any],
        method: str | None = None,
    ) -> ParameterSource:
        """Determine where to extract parameter from using param classes"""
        # Check Body and its subclasses first (Form, File)
        if isinstance(param.default, Body):
            if isinstance(param.default, File):
                return ParameterSource.FILE
            elif isinstance(param.default, Form):
                return ParameterSource.FORM
            else:
                return ParameterSource.BODY
        # Check Param and its subclasses (Query, Path, Header, Cookie)
        elif isinstance(param.default, Param):
            # All Param subclasses have in_ class attribute
            return param.default.in_
        # Fallback checks based on annotation or context
        elif param.annotation == File:
            return ParameterSource.FILE
        elif name in path_params:
            return ParameterSource.PATH
        elif ParameterResolver._is_body_model_annotation(param.annotation):
            if method and method.upper() in NO_BODY_METHODS:
                return ParameterSource.QUERY
            return ParameterSource.BODY
        else:
            return ParameterSource.QUERY

    @staticmethod
    def _extract_value(
        name: str,
        param: inspect.Parameter,
        source: ParameterSource,
        request_data: RequestData,
    ) -> Any:
        """Extract value from request data based on source"""
        param_name = ParameterResolver._get_param_name(name, param)

        extraction_map = {
            ParameterSource.PATH: lambda: request_data.path_params.get(param_name),
            ParameterSource.QUERY: lambda: request_data.query_params.get(param_name),
            ParameterSource.HEADER: lambda: ParameterResolver._extract_header_value(
                param, param_name, request_data.headers
            ),
            ParameterSource.COOKIE: lambda: request_data.cookies.get(param_name),
            ParameterSource.FORM: lambda: request_data.form_data.get(param_name),
            ParameterSource.FILE: lambda: request_data.files.get(param_name),
            ParameterSource.BODY: lambda: request_data.body,
        }

        extractor = extraction_map.get(source)
        return extractor() if extractor else None

    @staticmethod
    def _extract_header_value(
        param: inspect.Parameter, param_name: str, headers: dict[str, str]
    ) -> str | None:
        """Extract header value with proper name conversion"""
        # Handle header name conversion
        header_name = param_name
        if isinstance(param.default, Header):
            if param.default.alias:
                header_name = param.default.alias
            elif param.default.convert_underscores:
                header_name = param_name.replace("_", "-")
        else:
            # Default behavior for non-Header params
            header_name = param_name.replace("_", "-")

        # Headers are case-insensitive
        return ParameterResolver._get_case_insensitive_header(headers, header_name)

    @staticmethod
    def _get_case_insensitive_header(
        headers: dict[str, str], header_name: str
    ) -> str | None:
        """Get header value in case-insensitive manner"""
        for key, value in headers.items():
            if key.lower() == header_name.lower():
                return value
        return None

    @staticmethod
    def _get_param_name(name: str, param: inspect.Parameter) -> str:
        """Get the actual parameter name to use (considering aliases)"""
        if isinstance(param.default, BaseParam) and param.default.alias:
            return param.default.alias
        return name

    @staticmethod
    def _is_required_param(param: inspect.Parameter) -> bool:
        """Check if parameter is required"""
        if isinstance(param.default, BaseParam):
            default_val = param.default.default
            result = default_val is ... or default_val is PydanticUndefined
            return result
        return param.default is inspect.Parameter.empty

    @staticmethod
    def _get_default_value(param: inspect.Parameter) -> Any:
        """Get default value for parameter"""
        if isinstance(param.default, BaseParam):
            default_val = param.default.default
            if default_val is ... or default_val is PydanticUndefined:
                return None
            return default_val
        elif param.default is not inspect.Parameter.empty:
            return param.default
        return None

    @staticmethod
    def _needs_validation(param: inspect.Parameter) -> bool:
        """Check if parameter needs validation"""
        # Always validate if it's a Param instance with constraints
        if isinstance(param.default, BaseParam):
            return True
        # Validate if it has a specific type annotation
        return param.annotation != inspect.Parameter.empty

    @staticmethod
    def _build_field_info(param: inspect.Parameter) -> tuple[Any, ...]:
        """Build field info for Pydantic model creation from Param instance"""
        param_obj = param.default
        annotation = (
            param.annotation if param.annotation != inspect.Parameter.empty else Any
        )

        field_kwargs = ParameterResolver._build_field_constraints(param_obj)
        default = param_obj.default if param_obj.default is not ... else ...

        if field_kwargs:
            return annotation, Field(default=default, **field_kwargs)
        else:
            return annotation, default

    @staticmethod
    def _process_numeric_constraints(
        constraint: Any, constraint_type: str, field_kwargs: dict[str, Any]
    ) -> None:
        """Process numeric constraints (gt, ge, lt, le, multiple_of)"""
        constraint_mapping = {
            "Gt": ("gt", "gt"),
            "Ge": ("ge", "ge"),
            "Lt": ("lt", "lt"),
            "Le": ("le", "le"),
            "MultipleOf": ("multiple_of", "multiple_of"),
        }

        if constraint_type in constraint_mapping:
            attr_name, field_name = constraint_mapping[constraint_type]
            if hasattr(constraint, attr_name):
                field_kwargs[field_name] = getattr(constraint, attr_name)

    @staticmethod
    def _process_string_constraints(
        constraint: Any, constraint_type: str, field_kwargs: dict[str, Any]
    ) -> None:
        """Process string constraints (min_length, max_length)"""
        if constraint_type == "MinLen" and hasattr(constraint, "min_length"):
            field_kwargs["min_length"] = constraint.min_length
        elif constraint_type == "MaxLen" and hasattr(constraint, "max_length"):
            field_kwargs["max_length"] = constraint.max_length

    @staticmethod
    def _process_pattern_constraint(
        constraint: Any, field_kwargs: dict[str, Any]
    ) -> None:
        """Process pattern constraint"""
        if hasattr(constraint, "pattern"):
            field_kwargs["pattern"] = constraint.pattern

    @staticmethod
    def _process_strict_mode(
        constraint: Any, constraint_type: str, field_kwargs: dict[str, Any]
    ) -> None:
        """Process strict mode constraint"""
        if constraint_type == "Strict":
            field_kwargs["strict"] = constraint.strict

    @staticmethod
    def _process_float_decimal_constraints(
        constraint: Any, field_kwargs: dict[str, Any]
    ) -> None:
        """Process float/decimal specific constraints"""
        float_decimal_attrs = ["allow_inf_nan", "max_digits", "decimal_places"]

        for attr in float_decimal_attrs:
            if hasattr(constraint, attr):
                field_kwargs[attr] = getattr(constraint, attr)

    @staticmethod
    def _process_metadata(param_obj: Param, field_kwargs: dict[str, Any]) -> None:
        """Process metadata fields (description, title)"""
        for meta in ["description", "title"]:
            value = getattr(param_obj, meta, None)
            if value is not None:
                field_kwargs[meta] = value

    @classmethod
    def _build_field_constraints(cls, param_obj: Param) -> dict[str, Any]:
        """Build field constraints from Param object"""
        field_kwargs: dict[str, Any] = {}
        metadata = getattr(param_obj, "metadata", [])

        for constraint in metadata:
            constraint_type = type(constraint).__name__

            # Process different types of constraints
            cls._process_numeric_constraints(constraint, constraint_type, field_kwargs)
            cls._process_string_constraints(constraint, constraint_type, field_kwargs)
            cls._process_pattern_constraint(constraint, field_kwargs)
            cls._process_strict_mode(constraint, constraint_type, field_kwargs)
            cls._process_float_decimal_constraints(constraint, field_kwargs)

        # Process metadata
        cls._process_metadata(param_obj, field_kwargs)

        return field_kwargs

    @staticmethod
    def _is_pydantic_model(annotation: Any) -> bool:
        """Check if annotation is a Pydantic model"""
        return is_pydantic_model(annotation)

    @staticmethod
    def _is_body_model_annotation(annotation: Any) -> bool:
        """Check if annotation is a model or a container of models
        (list[Model], Model | None, list[Model] | None, ...)"""
        return is_body_model_annotation(annotation)

    @staticmethod
    def _coerce_scalar_to_list(value: Any, annotation: Any) -> Any:
        """Wrap a scalar into a one-item list for list-typed params"""
        if isinstance(value, list):
            return value
        target = annotation
        if hasattr(target, "__metadata__"):
            target = target.__origin__
        origin = typing.get_origin(target)
        if origin is typing.Union or origin is types.UnionType:
            args = [a for a in typing.get_args(target) if a is not type(None)]
            if len(args) == 1:
                target = args[0]
                origin = typing.get_origin(target)
        if origin is list:
            return [value]
        return value

    @staticmethod
    def _resolve_pydantic_model(
        model_class: type[BaseModel], data: dict[str, Any] | list[Any], param_name: str
    ) -> BaseModel:
        """Create Pydantic model instance from data"""
        try:
            if isinstance(data, list):
                raise ValidationError(
                    f"Validation error for parameter '{param_name}'",
                    "Expected JSON object, got array",
                )

            if not data:
                data = {}

            # Handle list fields that might come as single values
            data_copy = ParameterResolver._process_list_fields(model_class, data)
            return model_class(**data_copy)
        except PydanticValidationError as e:
            raise ValidationError(
                f"Validation error for parameter '{param_name}'", str(e)
            )

    @staticmethod
    def _process_list_fields(
        model_class: type[BaseModel], data: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle list fields that might come as single values"""
        data_copy = data.copy()

        if not hasattr(model_class, "model_fields"):
            return data_copy

        for field_name, field_info in model_class.model_fields.items():
            if (
                field_name in data_copy
                and not isinstance(data_copy[field_name], list)
                and hasattr(field_info, "annotation")
                and typing.get_origin(field_info.annotation) is list
            ):
                data_copy[field_name] = [data_copy[field_name]]

        return data_copy

    @classmethod
    def _get_or_create_validation_model(
        cls,
        owner: tuple[str, str],
        model_fields: dict[str, tuple[Any, ...] | None],
    ) -> type[BaseModel]:
        """Get or create validation model for given fields"""
        # Create cache key
        cache_key = frozenset(
            (owner[0], owner[1], name, str(field_info))
            for name, field_info in model_fields.items()
        )

        # Get or create model
        if cache_key not in cls._param_model_cache:

            class _ParamsBase(BaseModel):
                model_config = ConfigDict(arbitrary_types_allowed=True)

            cls._param_model_cache[cache_key] = create_model(
                "ParamsModel",
                __base__=_ParamsBase,
                **model_fields,  # type: ignore[call-overload]
            )

        return cls._param_model_cache[cache_key]

    @classmethod
    def _validate_parameters(
        cls,
        endpoint: Callable[..., Any],
        model_fields: dict[str, tuple[Any, ...] | None],
        model_values: dict[str, Any],
    ) -> dict[str, Any]:
        """Validate endpoint parameters using dynamic Pydantic model"""
        owner = (
            endpoint.__module__,
            getattr(endpoint, "__qualname__", endpoint.__name__),
        )
        return cls._validate_fields(owner, model_fields, model_values)

    @classmethod
    def _validate_fields(
        cls,
        owner: tuple[str, str],
        model_fields: dict[str, tuple[Any, ...] | None],
        model_values: dict[str, Any],
    ) -> dict[str, Any]:
        """Validate values against a dynamic Pydantic model.

        Values are returned via attribute access (not model_dump) so that
        nested models, files and rich types reach the endpoint as instances.
        """
        model_class = cls._get_or_create_validation_model(owner, model_fields)

        try:
            validated = model_class(**model_values)
        except PydanticValidationError as e:
            errors = e.errors()
            if errors:
                error_info = errors[0]
                param_name = str(error_info.get("loc", [""])[0])
                raise ValidationError(
                    f"Error parsing parameter '{param_name}'",
                    str(error_info.get("msg", "")),
                )
            raise ValidationError("Parameter validation failed", str(e))

        return {name: getattr(validated, name) for name in model_fields}
