from enum import Enum

SWAGGER_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.20.0/"
REDOC_URL = "https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"

# HTTP methods
SUPPORTED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]

# Type mappings
PYTHON_TYPE_MAPPING = {
    int: "integer",
    float: "number",
    bool: "boolean",
    str: "string",
}


class ParameterSource(Enum):
    """Source of parameter extraction"""

    PATH = "path"
    QUERY = "query"
    HEADER = "header"
    COOKIE = "cookie"
    BODY = "body"
    FORM = "form"
    FILE = "file"
