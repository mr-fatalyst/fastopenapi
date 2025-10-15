# TODO Temporary file to maintain backward compatibility
import warnings

warnings.warn(
    "Importing from fastopenapi.error_handler is deprecated. "
    "Use 'from fastopenapi.errors import ...' instead.",
    DeprecationWarning,
    stacklevel=2,
)
