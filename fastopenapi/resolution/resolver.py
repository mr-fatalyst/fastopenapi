import inspect
import typing
from collections.abc import Callable
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict
from pydantic import ValidationError as PydanticValidationError
from pydantic import create_model

from fastopenapi.core.types import Cookie, Form, Header, RequestData, UploadFile
from fastopenapi.errors.exceptions import BadRequestError, ValidationError


class ParameterSource(Enum):
    """Source of parameter extraction"""

    PATH = "path"
    QUERY = "query"
    HEADER = "header"
    COOKIE = "cookie"
    BODY = "body"
    FORM = "form"
    FILE = "file"


class ParameterResolver:
    """Resolve and validate endpoint parameters"""

    # Cache for dynamic models
    _param_model_cache: dict[frozenset, type[BaseModel]] = {}

    def resolve(self, endpoint: Callable, request_data: RequestData) -> dict[str, Any]:
        """Resolve all parameters for an endpoint"""
        sig = inspect.signature(endpoint)
        kwargs = {}

        # For collecting fields for dynamic validation
        model_fields = {}
        model_values = {}

        for name, param in sig.parameters.items():
            source = self._determine_source(name, param, request_data.path_params)

            # Handle Pydantic models
            if self._is_pydantic_model(param.annotation):
                kwargs[name] = self._resolve_pydantic_model(
                    param.annotation,
                    (
                        request_data.body
                        if source == ParameterSource.BODY
                        else request_data.query_params
                    ),
                    name,
                )
                continue

            # Extract value based on source
            value = self._extract_value(name, param, source, request_data)

            # Handle missing required parameters
            if value is None and param.default is inspect.Parameter.empty:
                raise BadRequestError(f"Missing required parameter: '{name}'")
            elif value is None:
                value = (
                    param.default
                    if not isinstance(param.default, (Header, Cookie, Form))
                    else None
                )

            # Collect for validation if value exists
            if value is not None:
                model_fields[name] = (
                    (
                        param.annotation
                        if param.annotation != inspect.Parameter.empty
                        else Any
                    ),
                    ...,
                )
                model_values[name] = value
            else:
                kwargs[name] = value

        # Validate collected parameters
        if model_fields:
            validated = self._validate_parameters(endpoint, model_fields, model_values)
            kwargs.update(validated)

        return kwargs

    def _determine_source(
        self, name: str, param: inspect.Parameter, path_params: dict
    ) -> ParameterSource:
        """Determine where to extract parameter from"""
        # Check for explicit markers
        if isinstance(param.default, Header):
            return ParameterSource.HEADER
        elif isinstance(param.default, Cookie):
            return ParameterSource.COOKIE
        elif isinstance(param.default, Form):
            return ParameterSource.FORM
        elif param.annotation == UploadFile:
            return ParameterSource.FILE
        elif name in path_params:
            return ParameterSource.PATH
        elif self._is_pydantic_model(param.annotation):
            return ParameterSource.BODY
        else:
            return ParameterSource.QUERY

    def _extract_value(
        self,
        name: str,
        param: inspect.Parameter,
        source: ParameterSource,
        request_data: RequestData,
    ) -> Any:
        """Extract value from request data based on source"""
        if source == ParameterSource.PATH:
            return request_data.path_params.get(name)
        elif source == ParameterSource.QUERY:
            return request_data.query_params.get(name)
        elif source == ParameterSource.HEADER:
            header_name = (
                param.default.alias
                if isinstance(param.default, Header) and param.default.alias
                else name
            )
            # Convert to header format (X-Api-Key from x_api_key)
            header_name = header_name.replace("_", "-").title()
            return request_data.headers.get(header_name.lower())
        elif source == ParameterSource.COOKIE:
            return request_data.cookies.get(name)
        elif source == ParameterSource.FORM:
            return request_data.form_data.get(name)
        elif source == ParameterSource.FILE:
            return request_data.files.get(name)
        elif source == ParameterSource.BODY:
            return request_data.body
        return None

    @staticmethod
    def _is_pydantic_model(annotation) -> bool:
        """Check if annotation is a Pydantic model"""
        return isinstance(annotation, type) and issubclass(annotation, BaseModel)

    def _resolve_pydantic_model(
        self, model_class: type[BaseModel], data: dict, param_name: str
    ):
        """Create Pydantic model instance from data"""
        try:
            if not data:
                data = {}

            # Handle list fields that might come as single values
            data_copy = data.copy()
            if hasattr(model_class, "model_fields"):
                for field_name, field_info in model_class.model_fields.items():
                    if (
                        field_name in data_copy
                        and not isinstance(data_copy[field_name], list)
                        and hasattr(field_info, "annotation")
                        and typing.get_origin(field_info.annotation) is list
                    ):
                        data_copy[field_name] = [data_copy[field_name]]

            return model_class(**data_copy)
        except Exception as e:
            raise ValidationError(
                f"Validation error for parameter '{param_name}'", str(e)
            )

    def _validate_parameters(
        self, endpoint: Callable, model_fields: dict, model_values: dict
    ) -> dict[str, Any]:
        """Validate parameters using dynamic Pydantic model"""
        # Create cache key
        cache_key = frozenset(
            (endpoint.__module__, endpoint.__name__, name, str(ann))
            for name, (ann, _) in model_fields.items()
        )

        # Get or create model
        if cache_key not in self._param_model_cache:

            class _ParamsBase(BaseModel):
                model_config = ConfigDict(arbitrary_types_allowed=True)

            self._param_model_cache[cache_key] = create_model(
                "ParamsModel",
                __base__=_ParamsBase,
                **model_fields,
            )
        try:
            validated = self._param_model_cache[cache_key](**model_values)
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
