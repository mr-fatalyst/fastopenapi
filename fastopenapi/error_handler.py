# Deprecation shim for the pre-1.0 import path; keep until 2.0
import warnings

warnings.warn(
    "Importing from fastopenapi.error_handler is deprecated. "
    "Use 'from fastopenapi.errors import ...' instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Export classes for backward compatibility but hide from IDE autocomplete
from fastopenapi.errors import (  # noqa: F401, E402
    APIError,
    AuthenticationError,
    AuthorizationError,
    BadRequestError,
    CircularDependencyError,
    DependencyError,
    ErrorType,
    InternalServerError,
    ResourceConflictError,
    ResourceNotFoundError,
    SecurityError,
    ServiceUnavailableError,
    ValidationError,
)
