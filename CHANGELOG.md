# Changelog

All notable changes to FastOpenAPI are documented in this file.

FastOpenAPI follows the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format.

## [1.0.0b1] - Unreleased

### Added

- **Dependency Injection system** with `Depends` and `Security` for automatic dependency resolution
  - Request-scoped caching (same dependency called multiple times returns cached result)
  - Circular dependency detection
  - `SecurityScopes` injection for OAuth2 scope validation
  - Generator/yield dependencies with proper cleanup (sync and async)
- **FastAPI-style parameter classes**: `Query`, `Path`, `Header`, `Cookie`, `Body`, `Form`, `File`
  - Full Pydantic v2 validation: `gt`, `ge`, `lt`, `le`, `min_length`, `max_length`, `pattern`, `multiple_of`, `strict`, etc.
  - Parameter metadata: `description`, `title`, `example`, `examples`, `deprecated`
  - Alias support for headers and query parameters
- **Django support** with `DjangoRouter` (sync) and `DjangoAsyncRouter` (async), including `urls` property for Django URL patterns
- **Falcon async support** with `FalconAsyncRouter` (in addition to existing sync `FalconRouter`)
- `FileUpload` class for framework-agnostic file handling with `.read()` and `.aread()` methods
- Form data and file upload extraction for all frameworks
- `RequestData` unified container for request data across all frameworks
- `Response` class for custom responses with headers and status codes
- Response model validation via `TypeAdapter` with thread-safe caching
- **Standardized error hierarchy**: `APIError`, `BadRequestError`, `ValidationError` (422), `AuthenticationError`, `AuthorizationError`, `ResourceNotFoundError`, `ResourceConflictError`, `InternalServerError`, `ServiceUnavailableError`, `DependencyError`, `CircularDependencyError`, `SecurityError`
- `APIError.from_exception()` for converting any exception to standardized JSON format
- `EXCEPTION_MAPPER` on routers for framework-specific exception conversion (e.g., Django's `PermissionDenied` → `AuthorizationError`)
- Built-in OpenAPI security schemes: Bearer JWT, API Key (header/query), Basic Auth, OAuth2
- Custom security schemes via `security_scheme` parameter (accepts `SecuritySchemeType` enum or raw dict)
- Security scheme merging in `include_router()`
- `SecuritySchemeType` exported from `fastopenapi` for public use
- Documentation completely rewritten with guides, API reference, framework-specific pages, and examples

### Changed

- **Complete architecture refactor** from monolithic `base_router.py` to composition-based modular design:
  - `core/` — `BaseRouter`, parameter classes, dependency resolver, types, constants
  - `resolution/` — `ParameterResolver` (extracted from `BaseRouter.resolve_endpoint_params()`)
  - `response/` — `ResponseBuilder` (extracted from `BaseRouter._serialize_response()`)
  - `openapi/` — `OpenAPIGenerator`, `SchemaBuilder`, UI renderers (extracted from `BaseRouter.generate_openapi()`)
  - `errors/` — error hierarchy (extracted from `error_handler.py`)
  - `routers/` — `BaseAdapter` + per-framework packages with separate extractors
- All framework routers now inherit from `BaseAdapter` instead of `BaseRouter`
- Each framework router split into separate router and extractor modules
- Route metadata stored in `RouteInfo` class (was tuple)
- Validation errors now return HTTP 422 (was 400)
- OpenAPI `summary` resolved from route metadata or formatted endpoint name; `description` from metadata or docstring
- Improved import errors with `MissingRouter` raising `ImportError` when framework is not installed
- `django` added as optional dependency extra

### Deprecated

- Importing from `fastopenapi.error_handler` module (use `from fastopenapi.errors import ...` instead)

### Removed

- `BaseRouter.generate_openapi()` method (use `router.openapi` property)
- `BaseRouter.resolve_endpoint_params()` and `BaseRouter._serialize_response()` internal methods
- Multi-language documentation (single English version retained)


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
