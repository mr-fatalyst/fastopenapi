# Changelog

All notable changes to FastOpenAPI are documented in this file.

FastOpenAPI follows the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format.

## [1.0.0b1] - Unreleased

### Added

- **Dependency Injection system** with `Depends` and `Security` classes for automatic dependency resolution
- Request-scoped dependency caching with circular dependency detection
- Security scopes validation with OAuth2 support
- **FastAPI-style parameter classes**: `Query`, `Path`, `Header`, `Cookie`, `Body`, `Form`, `File`
- Full Pydantic v2 validation support for all parameter types (gt, ge, lt, le, min_length, max_length, pattern, etc)
- Parameter documentation support (description, examples, deprecated flags)
- Pre-defined parameter types: `PositiveInt`, `NonNegativeInt`, `PositiveFloat`, `NonEmptyStr`, `LimitedStr`
- `FileUpload` class for framework-agnostic file handling with `.read()` and `.aread()` methods
- `RequestData` unified container for request data across all frameworks
- `Response` class for custom responses with headers and status codes
- **Django support** with `DjangoRouter` (sync) and `DjangoAsyncRouter` (async)
- Built-in OpenAPI security scheme definitions: Bearer JWT, API Key (header/query), Basic Auth, OAuth2
- Configurable security schemes via `security_scheme` parameter in router constructor
- Automatic security scheme integration in OpenAPI documentation
- `APIError.from_exception()` method for converting any exception to standardized format
- Thread-safe caching for parameter models, function signatures, and Pydantic schemas
- Modular architecture with dedicated packages: `core/`, `errors/`, `openapi/`, `resolution/`, `response/`, `routers/`
- `RouteInfo` dataclass for type-safe route metadata
- Enhanced OpenAPI schema generation with `SchemaBuilder`, `ParameterProcessor`, and `ResponseBuilder` helper classes
- Comprehensive error schema generation in OpenAPI documentation
- Support for all parameter sources in OpenAPI (path, query, header, cookie, body, form, file)

### Changed

- **Complete architecture refactor** from monolithic to modular design using composition over inheritance
- Router implementation changed from inheritance-based to composition-based using `BaseAdapter` pattern
- Moved parameter resolution from `BaseRouter.resolve_endpoint_params()` to dedicated `ParameterResolver` class
- Moved OpenAPI generation from `BaseRouter.generate_openapi()` to dedicated `OpenAPIGenerator` class
- Moved response serialization from `BaseRouter._serialize_response()` to `ResponseBuilder` class
- Split OpenAPI generation into focused helper classes for better separation of concerns
- Reorganized error handling from `error_handler.py` module to `errors/` package
- Split `base_router.py` into multiple focused modules with single responsibility
- Route metadata structure changed from tuple to `RouteInfo` dataclass for better type safety
- Router constructor signature updated with `security_scheme` parameter (default: `SecuritySchemeType.BEARER_JWT`)

### Deprecated

- Importing from `fastopenapi.error_handler` module (use `from fastopenapi.errors import ...` instead) - will show deprecation warning

### Removed
- `BaseRouter.generate_openapi()` method (use `router.openapi` property instead)
- Internal API methods for custom router developers: `resolve_endpoint_params()` and `_serialize_response()`


## [0.7.0] - 2025-04-27

### Changed
- Replaced `json.dumps/json.loads` with pydantic_core `to_json/from_json`
- `_serialize_response`: model list mapping now handled by Pydantic instead of manual recursion

### Fixed
- Issue with parsing repeated query parameters in URL.

### Removed
- The `use_aliases` from `BaseRouter` and reverted changes from 0.6.0.

## [0.6.0] – 2025‑04‑16

### Added
- The `use_aliases` parameter was added to the `BaseRouter` constructor. Default is `True`. To preserve the previous behavior (without using aliases from Pydantic), set `use_aliases=False`.
- support for Pydantic models with `alias=` by [PR #8](https://github.com/mr-fatalyst/fastopenapi/pull/8)

### Changed
- The `_serialize_response method` is now an instance method (was a `@staticmethod`) — to support `use_aliases`.
- The `_get_model_schema` method was temporarily changed from a `@classmethod` to a regular method — for consistent behavior with `use_aliases`.

### Deprecated
- `use_aliases` is deprecated and will be removed in version 0.7.0.

## [0.5.0] - 2025-04-13

### Added
- `AioHttpRouter` for integration with the `AioHttp` framework
- Class-level cache for model schemas
- `response_errors` for routers
- `error_handler` for standard error responses
- Some python types as response_model (`int`, `float`, `bool`, `str`)

## [0.4.0] - 2025-03-20

### Added
- `ReDoc UI` and default URL (`host:port/redoc`)
- `TornadoRouter` for integration with the `Tornado` framework

### Changed
- Revised and updated all tests.

### Fixed
- Status code for error response fixed: 422 -> 500

### Removed
- Removed the `add_docs_route` and `add_openapi_route` from `BaseRouter`.

## [0.3.1] - 2025-03-15

### Fixed
- router imports `ModuleNotFoundError`

## [0.3.0] - 2025-03-15

### Added
- `QuartRouter` for integration with the `Quart` framework.
- Initial Documentation

### Changed
- Import of routers. You can use `from fastopenapi.routers import YourRouter`

### Fixed
- Fixed retrieving parameters for BaseModel as arguments in GET routes.

## [0.2.1] - 2025-03-12

### Fixed
- Fixed an issue in `_serialize_response` where `BaseModel` was converted to a dictionary incorrectly.
- Resolved a bug causing `DataLoader` to crash when processing empty datasets.
- Added tests.
- Added `CHANGELOG.md`

## [0.2.0] - 2025-03-11

### Added
- Implemented `resolve_endpoint_params` in `BaseRouter`.
- Added the `prefix` parameter to the `include_router` method.
- Implemented `status_code` support for responses.

### Changed
- Refactored all routers.

### Removed
- Removed the `register_routes` method from `Starlette`.

## [0.1.0] - 2025-03-01

### Added
- Initial release of FastOpenAPI.
- Implemented core modules: `base`, `falcon`, `flask`, `sanic`, `starlette`.
- Added basic documentation and tests.
