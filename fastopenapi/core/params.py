"""
FastAPI-compatible parameter system for FastOpenAPI
Pydantic v2 only, no deprecated features
"""

import copy
import inspect
import types
import typing
from collections.abc import Callable, Sequence
from typing import Any

from pydantic import BaseModel
from pydantic.fields import FieldInfo

from fastopenapi.core.constants import ParameterSource


class BaseParam(FieldInfo):
    """Base parameter class extending Pydantic FieldInfo"""

    def __init__(
        self,
        default: Any = ...,
        *,
        alias: str | None = None,
        title: str | None = None,
        description: str | None = None,
        gt: float | None = None,
        ge: float | None = None,
        lt: float | None = None,
        le: float | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
        pattern: str | None = None,
        strict: bool | None = None,
        multiple_of: float | None = None,
        allow_inf_nan: bool | None = None,
        max_digits: int | None = None,
        decimal_places: int | None = None,
        example: Any | None = None,
        examples: list[Any] | None = None,
        deprecated: bool | None = None,
        include_in_schema: bool = True,
        json_schema_extra: dict[str, Any] | None = None,
        **extra: Any,
    ):
        # Build kwargs for FieldInfo
        kwargs = {
            "default": default,
            "alias": alias,
            "title": title,
            "description": description,
            "gt": gt,
            "ge": ge,
            "lt": lt,
            "le": le,
            "min_length": min_length,
            "max_length": max_length,
            "pattern": pattern,
            "strict": strict,
            "multiple_of": multiple_of,
            "allow_inf_nan": allow_inf_nan,
            "max_digits": max_digits,
            "decimal_places": decimal_places,
            "deprecated": deprecated,
            "json_schema_extra": json_schema_extra,
            **extra,
        }

        # Filter out None values
        filtered_kwargs = {
            k: v for k, v in kwargs.items() if v is not None or k == "default"
        }

        super().__init__(**filtered_kwargs)

        self.example = example
        self.examples = examples
        self.include_in_schema = include_in_schema

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.default})"


class Param(BaseParam):
    """Base parameter class for URL/header/cookie parameters.

    Subclasses only pin their location (``in_``) and default; the full
    keyword set is documented once on BaseParam and passed through.
    """

    in_: ParameterSource


class Query(Param):
    """Query parameter from URL query string"""

    in_ = ParameterSource.QUERY

    def __init__(self, default: Any = None, **kwargs: Any):
        super().__init__(default, **kwargs)


class Path(Param):
    """Path parameter from URL path"""

    in_ = ParameterSource.PATH

    def __init__(self, default: Any = ..., **kwargs: Any):
        # Path parameters cannot have defaults
        if default is not ...:
            raise ValueError("Path parameters cannot have a default value")
        super().__init__(default, **kwargs)


class Header(Param):
    """Header parameter from HTTP headers"""

    in_ = ParameterSource.HEADER

    def __init__(
        self,
        default: Any = None,
        *,
        convert_underscores: bool = True,
        **kwargs: Any,
    ):
        self.convert_underscores = convert_underscores
        super().__init__(default, **kwargs)


class Cookie(Param):
    """Cookie parameter from HTTP cookies"""

    in_ = ParameterSource.COOKIE

    def __init__(self, default: Any = None, **kwargs: Any):
        super().__init__(default, **kwargs)


class Body(BaseParam):
    """Body parameter for JSON request bodies"""

    def __init__(
        self,
        default: Any = None,
        *,
        embed: bool | None = None,
        media_type: str = "application/json",
        **kwargs: Any,
    ):
        super().__init__(default, **kwargs)
        self.embed = embed
        self.media_type = media_type


class Form(Body):
    """Form data parameter"""

    def __init__(
        self,
        default: Any = None,
        *,
        media_type: str = "application/x-www-form-urlencoded",
        **kwargs: Any,
    ):
        super().__init__(default, media_type=media_type, **kwargs)


class File(Form):
    """File upload parameter"""

    def __init__(
        self,
        default: Any = None,
        *,
        media_type: str = "multipart/form-data",
        **kwargs: Any,
    ):
        super().__init__(default, media_type=media_type, **kwargs)


class Depends:
    """Dependency injection marker"""

    def __init__(self, dependency: Callable[..., Any] | None = None):
        self.dependency = dependency

    def __repr__(self) -> str:
        name = getattr(self.dependency, "__name__", type(self.dependency).__name__)
        return f"{self.__class__.__name__}({name})"


class Security(Depends):
    """Security dependency with scopes"""

    def __init__(
        self,
        dependency: Callable[..., Any] | None = None,
        *,
        scopes: Sequence[str] | None = None,
    ):
        super().__init__(dependency=dependency)
        self.scopes = list(scopes) if scopes else []


class SecurityScopes:
    """Required scopes injected into security dependency functions"""

    def __init__(self, scopes: list[str] | None = None):
        self.scopes = scopes or []


def is_pydantic_model(annotation: Any) -> bool:
    """Check if annotation is a Pydantic model class"""
    return isinstance(annotation, type) and issubclass(annotation, BaseModel)


def is_body_model_annotation(annotation: Any) -> bool:
    """Check if annotation is a model or a container of models
    (list[Model], Model | None, list[Model] | None, ...).

    Single source of truth for the resolver and the OpenAPI generator —
    their body-vs-query decisions must never drift apart.
    """
    if is_pydantic_model(annotation):
        return True
    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)
    if origin is list:
        return bool(args) and is_body_model_annotation(args[0])
    if origin is typing.Union or origin is types.UnionType:
        return any(
            is_body_model_annotation(arg) for arg in args if arg is not type(None)
        )
    return False


def unwrap_annotated_parameter(param: inspect.Parameter) -> inspect.Parameter:
    """Extract a Param/Depends marker from Annotated[...] metadata.

    Turns ``x: Annotated[int, Query(ge=1)] = 5`` into the equivalent of
    ``x: int = Query(ge=1, default=5)`` so the rest of the pipeline sees
    the default-value declaration style.
    """
    metadata = getattr(param.annotation, "__metadata__", None)
    if not metadata:
        return param

    marker = None
    for meta in metadata:
        if isinstance(meta, (BaseParam, Depends)):
            marker = meta
    if marker is None:
        return param

    base_type = param.annotation.__origin__

    if isinstance(marker, Depends):
        return param.replace(annotation=base_type, default=marker)

    field = copy.copy(marker)
    if param.default is not inspect.Parameter.empty:
        field.default = param.default
    return param.replace(annotation=base_type, default=field)
