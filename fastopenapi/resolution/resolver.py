import inspect
import typing
from collections.abc import Callable
from types import MappingProxyType
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic import ValidationError as PydanticValidationError
from pydantic import create_model
from pydantic_core import PydanticUndefined

from fastopenapi.core.constants import ParameterSource
from fastopenapi.core.dependency_resolver import dependency_resolver
from fastopenapi.core.params import (
    BaseParam,
    Body,
    Cookie,
    Depends,
    File,
    Form,
    Header,
    Param,
    Security,
)
from fastopenapi.core.types import RequestData
from fastopenapi.errors.exceptions import BadRequestError, ValidationError


class ProcessedParameter:
    """Container for processed parameter information"""

    def __init__(
        self,
        value: Any,
        needs_validation: bool = False,
        field_info: tuple | None = None,
    ):
        self.value = value
        self.needs_validation = needs_validation
        self.field_info = field_info


class ParameterResolver:
    """Resolve and validate endpoint parameters"""

    # Cache for dynamic models
    _param_model_cache: dict[frozenset, type[BaseModel]] = {}
    # Cache endpoint signature
    _signature_cache: dict[Callable, MappingProxyType] = {}

    @classmethod
    def _get_signature(cls, endpoint) -> typing.ItemsView:
        """Get cached signature parameters for endpoint"""
        cached_params = cls._signature_cache.get(endpoint)
        if cached_params:
            return cached_params.items()
        else:
            sig = inspect.signature(endpoint)
            cls._signature_cache[endpoint] = sig.parameters
        return cls._signature_cache[endpoint].items()

    @classmethod
    def resolve(cls, endpoint: Callable, request_data: RequestData) -> dict[str, Any]:
        """Resolve all parameters for an endpoint"""
        params = cls._get_signature(endpoint)
        kwargs = {}

        # Resolve dependencies first
        kwargs.update(cls._resolve_dependencies(endpoint, request_data))

        # Process regular parameters
        regular_kwargs, model_fields, model_values = cls._process_parameters(
            params, request_data
        )
        kwargs.update(regular_kwargs)

        # Validate collected parameters
        if model_fields:
            validated_params = cls._validate_parameters(
                endpoint, model_fields, model_values
            )
            kwargs.update(validated_params)

        return kwargs

    @staticmethod
    def _resolve_dependencies(
        endpoint: Callable, request_data: RequestData
    ) -> dict[str, Any]:
        """Resolve endpoint dependencies"""
        try:
            return dependency_resolver.resolve_dependencies(endpoint, request_data)
        except Exception:
            # Re-raise dependency errors as-is
            raise

    @classmethod
    def _process_parameters(
        cls, params: typing.ItemsView, request_data: RequestData
    ) -> tuple[dict[str, Any], dict[str, tuple], dict[str, Any]]:
        """Process all endpoint parameters"""
        regular_kwargs = {}
        model_fields = {}
        model_values = {}

        for name, param in params:
            # Skip dependency parameters - already resolved
            if isinstance(param.default, (Depends, Security)):
                continue

            processed_param = cls._process_single_parameter(name, param, request_data)

            if processed_param.needs_validation:
                model_fields[name] = processed_param.field_info
                model_values[name] = processed_param.value
            else:
                regular_kwargs[name] = processed_param.value

        return regular_kwargs, model_fields, model_values

    @classmethod
    def _process_single_parameter(
        cls, name: str, param: inspect.Parameter, request_data: RequestData
    ) -> ProcessedParameter:
        """Process a single parameter"""
        source = cls._determine_source(name, param, request_data.path_params)

        # Handle Pydantic models
        if cls._is_pydantic_model(param.annotation):
            data = (
                request_data.body
                if source == ParameterSource.BODY
                else request_data.query_params
            )
            resolved_model = cls._resolve_pydantic_model(param.annotation, data, name)
            return ProcessedParameter(value=resolved_model, needs_validation=False)

        # Extract value based on source
        value = cls._extract_value(name, param, source, request_data)

        # Handle missing required parameters
        if value is None and cls._is_required_param(param):
            param_name = cls._get_param_name(name, param)
            raise BadRequestError(f"Missing required parameter: '{param_name}'")
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
        name: str, param: inspect.Parameter, path_params: dict[str, Any]
    ) -> ParameterSource:
        """Determine where to extract parameter from using param classes"""
        # Check if it's one of our parameter classes
        if isinstance(param.default, Param):
            return param.default.in_
        elif isinstance(param.default, Header):
            return ParameterSource.HEADER
        elif isinstance(param.default, Cookie):
            return ParameterSource.COOKIE
        elif isinstance(param.default, Form):
            return ParameterSource.FORM
        elif isinstance(param.default, Body):
            return ParameterSource.BODY
        elif param.annotation == File:
            return ParameterSource.FILE
        elif name in path_params:
            return ParameterSource.PATH
        elif ParameterResolver._is_pydantic_model(param.annotation):
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
    def _build_field_info(param: inspect.Parameter) -> tuple:
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
        constraint, constraint_type: str, field_kwargs: dict
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
        constraint, constraint_type: str, field_kwargs: dict
    ) -> None:
        """Process string constraints (min_length, max_length)"""
        if constraint_type == "MinLen" and hasattr(constraint, "min_length"):
            field_kwargs["min_length"] = constraint.min_length
        elif constraint_type == "MaxLen" and hasattr(constraint, "max_length"):
            field_kwargs["max_length"] = constraint.max_length

    @staticmethod
    def _process_pattern_constraint(constraint, field_kwargs: dict) -> None:
        """Process pattern constraint"""
        if hasattr(constraint, "pattern"):
            field_kwargs["pattern"] = constraint.pattern

    @staticmethod
    def _process_strict_mode(
        constraint, constraint_type: str, field_kwargs: dict
    ) -> None:
        """Process strict mode constraint"""
        if constraint_type == "Strict":
            field_kwargs["strict"] = constraint.strict

    @staticmethod
    def _process_float_decimal_constraints(constraint, field_kwargs: dict) -> None:
        """Process float/decimal specific constraints"""
        float_decimal_attrs = ["allow_inf_nan", "max_digits", "decimal_places"]

        for attr in float_decimal_attrs:
            if hasattr(constraint, attr):
                field_kwargs[attr] = getattr(constraint, attr)

    @staticmethod
    def _process_metadata(param_obj: Param, field_kwargs: dict) -> None:
        """Process metadata fields (description, title)"""
        for meta in ["description", "title"]:
            value = getattr(param_obj, meta, None)
            if value is not None:
                field_kwargs[meta] = value

    @classmethod
    def _build_field_constraints(cls, param_obj: Param) -> dict[str, Any]:
        """Build field constraints from Param object"""
        field_kwargs = {}
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
    def _is_pydantic_model(annotation) -> bool:
        """Check if annotation is a Pydantic model"""
        return isinstance(annotation, type) and issubclass(annotation, BaseModel)

    @staticmethod
    def _resolve_pydantic_model(
        model_class: type[BaseModel], data: dict[str, Any], param_name: str
    ) -> BaseModel:
        """Create Pydantic model instance from data"""
        try:
            if not data:
                data = {}

            # Handle list fields that might come as single values
            data_copy = ParameterResolver._process_list_fields(model_class, data)
            return model_class(**data_copy)
        except Exception as e:
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
        cls, endpoint: Callable, model_fields: dict[str, tuple]
    ) -> type[BaseModel]:
        """Get or create validation model for given fields"""
        # Create cache key
        cache_key = frozenset(
            (endpoint.__module__, endpoint.__name__, name, str(field_info))
            for name, field_info in model_fields.items()
        )

        # Get or create model
        if cache_key not in cls._param_model_cache:

            class _ParamsBase(BaseModel):
                model_config = ConfigDict(arbitrary_types_allowed=True)

            cls._param_model_cache[cache_key] = create_model(
                "ParamsModel",
                __base__=_ParamsBase,
                **model_fields,
            )

        return cls._param_model_cache[cache_key]

    @classmethod
    def _validate_parameters(
        cls,
        endpoint: Callable,
        model_fields: dict[str, tuple],
        model_values: dict[str, Any],
    ) -> dict[str, Any]:
        """Validate parameters using dynamic Pydantic model"""
        model_class = cls._get_or_create_validation_model(endpoint, model_fields)

        try:
            validated = model_class(**model_values)
            return validated.model_dump()
        except PydanticValidationError as e:
            errors = e.errors()
            if errors:
                error_info = errors[0]
                param_name = str(error_info.get("loc", [""])[0])
                raise BadRequestError(
                    f"Error parsing parameter '{param_name}'",
                    str(error_info.get("msg", "")),
                )
            raise BadRequestError("Parameter validation failed", str(e))
