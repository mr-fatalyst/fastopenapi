# Changelog

All notable changes to FastOpenAPI are documented in this file.

FastOpenAPI follows the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format.

## [0.3.0] - Unreleased

### Added
- `QuartRouter` for integration with the `Quart` framework.

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
- Initial release of the library.
- Implemented core modules: `base`, `falcon`, `flask`, `sanic`, `starlette`.
- Added basic documentation and tests.
