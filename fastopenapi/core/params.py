"""
FastAPI-compatible parameter system for FastOpenAPI
Pydantic v2 only, no deprecated features
"""

from collections.abc import Callable, Sequence
from typing import Annotated, Any

from pydantic import Field
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
        examples: list[Any] | None = None,
        deprecated: bool | None = None,
        include_in_schema: bool = True,
        json_schema_extra: dict[str, Any] | None = None,
        **extra: Any,
    ):
        # OpenAPI specific attributes
        self.examples = examples
        self.include_in_schema = include_in_schema

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

        self.examples = examples
        self.include_in_schema = include_in_schema

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.default})"


class Param(BaseParam):
    """Base parameter class for URL/header/cookie parameters"""

    in_: ParameterSource

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
        examples: list[Any] | None = None,
        deprecated: bool | None = None,
        include_in_schema: bool = True,
        json_schema_extra: dict[str, Any] | None = None,
        **extra: Any,
    ):
        super().__init__(
            default=default,
            alias=alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            pattern=pattern,
            strict=strict,
            multiple_of=multiple_of,
            allow_inf_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            examples=examples,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            json_schema_extra=json_schema_extra,
            **extra,
        )


class Query(Param):
    """Query parameter from URL query string"""

    in_ = ParameterSource.QUERY

    def __init__(
        self,
        default: Any = None,
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
        examples: list[Any] | None = None,
        deprecated: bool | None = None,
        include_in_schema: bool = True,
        json_schema_extra: dict[str, Any] | None = None,
        **extra: Any,
    ):
        super().__init__(
            default=default,
            alias=alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            pattern=pattern,
            strict=strict,
            multiple_of=multiple_of,
            allow_inf_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            examples=examples,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            json_schema_extra=json_schema_extra,
            **extra,
        )


class Path(Param):
    """Path parameter from URL path"""

    in_ = ParameterSource.PATH

    def __init__(
        self,
        default: Any = ...,  # Path params must be required
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
        examples: list[Any] | None = None,
        deprecated: bool | None = None,
        include_in_schema: bool = True,
        json_schema_extra: dict[str, Any] | None = None,
        **extra: Any,
    ):
        # Path parameters cannot have defaults
        if default is not ...:
            raise ValueError("Path parameters cannot have a default value")

        super().__init__(
            default=default,
            alias=alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            pattern=pattern,
            strict=strict,
            multiple_of=multiple_of,
            allow_inf_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            examples=examples,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            json_schema_extra=json_schema_extra,
            **extra,
        )


class Header(Param):
    """Header parameter from HTTP headers"""

    in_ = ParameterSource.HEADER

    def __init__(
        self,
        default: Any = None,
        *,
        alias: str | None = None,
        convert_underscores: bool = True,
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
        examples: list[Any] | None = None,
        deprecated: bool | None = None,
        include_in_schema: bool = True,
        json_schema_extra: dict[str, Any] | None = None,
        **extra: Any,
    ):
        self.convert_underscores = convert_underscores

        super().__init__(
            default=default,
            alias=alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            pattern=pattern,
            strict=strict,
            multiple_of=multiple_of,
            allow_inf_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            examples=examples,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            json_schema_extra=json_schema_extra,
            **extra,
        )


class Cookie(Param):
    """Cookie parameter from HTTP cookies"""

    in_ = ParameterSource.COOKIE

    def __init__(
        self,
        default: Any = None,
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
        examples: list[Any] | None = None,
        deprecated: bool | None = None,
        include_in_schema: bool = True,
        json_schema_extra: dict[str, Any] | None = None,
        **extra: Any,
    ):
        super().__init__(
            default=default,
            alias=alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            pattern=pattern,
            strict=strict,
            multiple_of=multiple_of,
            allow_inf_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            examples=examples,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            json_schema_extra=json_schema_extra,
            **extra,
        )


class Body(BaseParam):
    """Body parameter for JSON request bodies"""

    def __init__(
        self,
        default: Any = None,
        *,
        embed: bool | None = None,
        media_type: str = "application/json",
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
        examples: list[Any] | None = None,
        deprecated: bool | None = None,
        include_in_schema: bool = True,
        json_schema_extra: dict[str, Any] | None = None,
        **extra: Any,
    ):
        self.embed = embed
        self.media_type = media_type

        super().__init__(
            default=default,
            alias=alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            pattern=pattern,
            strict=strict,
            multiple_of=multiple_of,
            allow_inf_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            examples=examples,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            json_schema_extra=json_schema_extra,
            **extra,
        )

        self.embed = embed
        self.media_type = media_type


class Form(Body):
    """Form data parameter"""

    def __init__(
        self,
        default: Any = None,
        *,
        media_type: str = "application/x-www-form-urlencoded",
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
        examples: list[Any] | None = None,
        deprecated: bool | None = None,
        include_in_schema: bool = True,
        json_schema_extra: dict[str, Any] | None = None,
        **extra: Any,
    ):
        super().__init__(
            default=default,
            media_type=media_type,
            alias=alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            pattern=pattern,
            strict=strict,
            multiple_of=multiple_of,
            allow_inf_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            examples=examples,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            json_schema_extra=json_schema_extra,
            **extra,
        )


class File(Form):
    """File upload parameter"""

    def __init__(
        self,
        default: Any = None,
        *,
        media_type: str = "multipart/form-data",
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
        examples: list[Any] | None = None,
        deprecated: bool | None = None,
        include_in_schema: bool = True,
        json_schema_extra: dict[str, Any] | None = None,
        **extra: Any,
    ):
        super().__init__(
            default=default,
            media_type=media_type,
            alias=alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            pattern=pattern,
            strict=strict,
            multiple_of=multiple_of,
            allow_inf_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            examples=examples,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            json_schema_extra=json_schema_extra,
            **extra,
        )


class Depends:
    """Dependency injection marker"""

    def __init__(
        self, dependency: Callable[..., Any] | None = None, *, use_cache: bool = True
    ):
        self.dependency = dependency
        self.use_cache = use_cache

    def __repr__(self) -> str:
        name = getattr(self.dependency, "__name__", type(self.dependency).__name__)
        cache_info = "" if self.use_cache else ", use_cache=False"
        return f"{self.__class__.__name__}({name}{cache_info})"


class Security(Depends):
    """Security dependency with scopes"""

    def __init__(
        self,
        dependency: Callable[..., Any] | None = None,
        *,
        scopes: Sequence[str] | None = None,
        use_cache: bool = True,
    ):
        super().__init__(dependency=dependency, use_cache=use_cache)
        self.scopes = list(scopes) if scopes else []


# Pre-defined common validation types
PositiveInt = Annotated[int, Field(gt=0, description="Positive integer")]
NonNegativeInt = Annotated[int, Field(ge=0, description="Non-negative integer")]
PositiveFloat = Annotated[float, Field(gt=0.0, description="Positive float")]
NonEmptyStr = Annotated[str, Field(min_length=1, description="Non-empty string")]
LimitedStr = Annotated[
    str, Field(min_length=1, max_length=255, description="Limited string")
]

# Common ID patterns
UserId = Annotated[int, Path(description="User ID", ge=1)]
ItemId = Annotated[int, Path(description="Item ID", ge=1)]

# Pagination patterns
PageQuery = Annotated[int, Query(description="Page number", ge=1)]
LimitQuery = Annotated[int, Query(description="Items per page", ge=1, le=100)]
OffsetQuery = Annotated[int, Query(description="Items to skip", ge=0)]
