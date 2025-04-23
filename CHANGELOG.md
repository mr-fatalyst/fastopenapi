# Changelog

All notable changes to FastOpenAPI are documented in this file.

FastOpenAPI follows the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format.

## [0.7.0] - Unreleased

### Fixed
- Fixed issue with parsing repeated query parameters in URL.

### Removed
- Removed the `use_aliases` from `BaseRouter` and reverted changes from 0.6.0.

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
