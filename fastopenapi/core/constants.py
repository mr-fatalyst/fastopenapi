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


class SecuritySchemeType(Enum):
    BEARER_JWT = "bearer_jwt"
    API_KEY_HEADER = "api_key_header"
    API_KEY_QUERY = "api_key_query"
    BASIC_AUTH = "basic_auth"
    OAUTH2 = "oauth2"


# OpenAPI security scheme names
SECURITY_SCHEME_NAMES = {
    SecuritySchemeType.BEARER_JWT: "BearerAuth",
    SecuritySchemeType.API_KEY_HEADER: "ApiKeyAuth",
    SecuritySchemeType.API_KEY_QUERY: "ApiKeyQuery",
    SecuritySchemeType.BASIC_AUTH: "BasicAuth",
    SecuritySchemeType.OAUTH2: "OAuth2",
}


SECURITY_SCHEMES = {
    SecuritySchemeType.BEARER_JWT: {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    },
    SecuritySchemeType.API_KEY_HEADER: {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
    },
    SecuritySchemeType.API_KEY_QUERY: {
        "type": "apiKey",
        "in": "query",
        "name": "api_key",
    },
    SecuritySchemeType.BASIC_AUTH: {
        "type": "http",
        "scheme": "basic",
    },
    SecuritySchemeType.OAUTH2: {
        "type": "oauth2",
        "flows": {
            "authorizationCode": {
                "authorizationUrl": "https://example.com/oauth/authorize",
                "tokenUrl": "https://example.com/oauth/token",
                "scopes": {
                    "read": "Read access",
                    "write": "Write access",
                    "admin": "Admin access",
                },
            }
        },
    },
}
