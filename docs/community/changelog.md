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

### Changed
- The `_serialize_response method` is now an instance method (was a `@staticmethod`) — to support `use_aliases`.
- The `_get_model_schema` method was temporarily changed from a `@classmethod` to a regular method — for consistent behavior with `use_aliases`.

### Deprecated
- `use_aliases` is deprecated and will be removed in version 0.7.0.


## [0.5.0] - 2025-04-13

### Added
- **AioHttpRouter** for integration with the AIOHTTP framework (async support for AIOHTTP).
- Class-level cache for model schemas to improve performance (avoids regenerating JSON Schema for the same Pydantic model repeatedly).
- `response_errors` parameter for route decorators to document error responses in OpenAPI.
- `error_handler` module for standard error responses (provides exceptions like `BadRequestError`, `ResourceNotFoundError`, etc., as described in documentation).
- Support for using basic Python types (`int`, `float`, `bool`, `str`) as `response_model` (for simple responses).

## [0.4.0] - 2025-03-20

### Added
- **ReDoc UI** support. A ReDoc documentation interface is now served at the default URL (e.g., `/redoc`).
- **TornadoRouter** for integration with the Tornado framework.

### Changed
- Revised and updated all tests to improve coverage and reliability.

### Fixed
- Status code for internal error responses: changed from 422 to 500 for unhandled exceptions, providing a more appropriate HTTP status for server errors.

### Removed
- Removed the `add_docs_route` and `add_openapi_route` methods from `BaseRouter`. Documentation routes are now added by default, so these manual methods are no longer needed.

## [0.3.1] - 2025-03-15

### Fixed
- Fixed import issue for routers when a framework is not installed. (Guarded against `ModuleNotFoundError` if an extra was not installed and its router was imported.)

## [0.3.0] - 2025-03-15

### Added
- **QuartRouter** for integration with the Quart framework (async Flask-like framework).
- Initial documentation (introduction and basic usage examples) added to repository.

### Changed
- Import syntax for routers simplified: you can now do `from fastopenapi.routers import YourRouter` (e.g., `FlaskRouter`) instead of deeper module paths.

### Fixed
- Fixed retrieving parameters for BaseModel arguments in GET routes. Query parameters based on Pydantic models now work correctly.

## [0.2.1] - 2025-03-12

### Fixed
- Fixed an issue in internal response serialization: `_serialize_response` now correctly handles `BaseModel` instances by converting them to dict before JSON encoding (preventing a TypeError).
- Resolved a bug causing `DataLoader` to crash when processing empty datasets. (This appears to be an internal utility, possibly used for schema generation.)
- Added more tests to cover these scenarios.
- Added this `CHANGELOG.md` file to track changes.

## [0.2.0] - 2025-03-11

### Added
- Implemented `resolve_endpoint_params` in `BaseRouter` to systematically resolve function parameters (path, query, body) and integrate with Pydantic validation.
- Added `prefix` parameter to the `include_router` method, allowing grouping routes under a path.
- Implemented `status_code` support for responses in route decorators (could specify default status code for each endpoint).

### Changed
- Refactored all router implementations for consistency and to reduce code duplication.

### Removed
- Removed the `register_routes` method from Starlette integration (no longer needed after refactor).

## [0.1.0] - 2025-03-01

### Added
- Initial release of FastOpenAPI.
- Core functionality implemented:
  - Base classes and structure for routers.
  - Router support for Falcon, Flask, Sanic, Starlette.
  - OpenAPI schema generation leveraging Pydantic v2.
  - Basic validation for query and body parameters.
- Included basic documentation in README and a few examples.
- Added initial test suite covering basic route registration and schema generation.
