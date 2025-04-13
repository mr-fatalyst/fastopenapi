# Changelog

All notable changes to FastOpenAPI will be documented in this file.

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
