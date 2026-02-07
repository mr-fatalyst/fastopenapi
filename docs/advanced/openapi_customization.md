# OpenAPI Customization

This guide covers customizing the OpenAPI schema generation in FastOpenAPI.

## Basic Configuration

Configure OpenAPI metadata when creating your router:

```python
from fastopenapi.routers import FlaskRouter

router = FlaskRouter(
    app=app,
    title="My API",
    version="2.0.0",
    description="A comprehensive API for managing resources",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_version="3.1.0"
)
```

## Supported Parameters

The router constructor supports the following parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `app` | Any | None | Framework application instance |
| `title` | str | "My App" | API title |
| `version` | str | "0.1.0" | API version |
| `description` | str | "API documentation" | API description |
| `docs_url` | str \| None | "/docs" | Swagger UI URL |
| `redoc_url` | str \| None | "/redoc" | ReDoc URL |
| `openapi_url` | str \| None | "/openapi.json" | OpenAPI schema URL |

> **Note:** Setting any URL to `None` disables all documentation endpoints at once.
| `openapi_version` | str | "3.0.0" | OpenAPI specification version |
| `security_scheme` | SecuritySchemeType \| None | BEARER_JWT | Default security scheme |

## Tags

Organize endpoints with tags:

```python
@router.get("/users", tags=["Users", "Public"])
def list_users():
    return []

@router.post("/users", tags=["Users", "Admin"])
def create_user(user: User):
    return user
```

### Tag Metadata

Tags are automatically collected from endpoints. Use the `tags` parameter in route decorators:

```python
@router.get("/users", tags=["Users"])
def list_users():
    return []

@router.get("/items", tags=["Items"])
def list_items():
    return []
```

## Operation Customization

### Operation ID

```python
@router.get("/users/{user_id}", operation_id="get_user_by_id")
def get_user(user_id: int):
    return {"id": user_id}
```

### Summary and Description

```python
@router.get(
    "/users/{user_id}",
    summary="Get a user",
    description="Retrieve a user by their unique ID"
)
def get_user(user_id: int):
    return {"id": user_id}
```

Or use docstrings:

```python
@router.get("/users/{user_id}")
def get_user(user_id: int):
    """
    Get a user by ID.
    
    This endpoint retrieves detailed information about a specific user.
    Requires authentication.
    """
    return {"id": user_id}
```

### Deprecation

Mark endpoints as deprecated:

```python
@router.get("/old-endpoint", deprecated=True)
def old_endpoint():
    """This endpoint is deprecated. Use /new-endpoint instead."""
    return {"message": "deprecated"}
```

## Response Documentation

### Multiple Response Codes

```python
@router.get(
    "/users/{user_id}",
    responses={
        200: {"description": "User found"},
        404: {"description": "User not found"},
        500: {"description": "Internal server error"}
    }
)
def get_user(user_id: int):
    user = database.get(user_id)
    if not user:
        raise ResourceNotFoundError("User not found")
    return user
```

### Response Models for Different Status Codes

```python
class UserResponse(BaseModel):
    id: int
    name: str

class ErrorResponse(BaseModel):
    error: str
    message: str

@router.get(
    "/users/{user_id}",
    responses={
        200: {"model": UserResponse, "description": "Successful response"},
        404: {"model": ErrorResponse, "description": "User not found"},
    }
)
def get_user(user_id: int):
    return UserResponse(id=user_id, name="John")
```

## Request Body Documentation

### Example Values

```python
class UserCreate(BaseModel):
    username: str = Field(..., example="johndoe")
    email: EmailStr = Field(..., example="john@example.com")
    age: int = Field(..., example=25, ge=0, le=120)

@router.post("/users")
def create_user(user: UserCreate):
    return user
```

### Multiple Examples

```python
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "username": "johndoe",
                    "email": "john@example.com"
                },
                {
                    "username": "janedoe",
                    "email": "jane@example.com"
                }
            ]
        }
    }
```

## Parameter Documentation

### Path Parameters

```python
from fastopenapi import Path

@router.get("/users/{user_id}")
def get_user(
    user_id: int = Path(
        ...,
        description="The unique identifier of the user",
        example=123,
        ge=1
    )
):
    return {"id": user_id}
```

### Query Parameters

```python
from fastopenapi import Query

@router.get("/users")
def list_users(
    page: int = Query(
        1,
        description="Page number",
        example=1,
        ge=1
    ),
    limit: int = Query(
        10,
        description="Number of items per page",
        example=10,
        ge=1,
        le=100
    )
):
    return []
```

## Security Schemes

### API Key in Header

```python
from fastopenapi.core.constants import SecuritySchemeType

router = FlaskRouter(
    app=app,
    title="My API",
    version="1.0.0",
    security_scheme=SecuritySchemeType.API_KEY_HEADER
)
```

### Bearer JWT

```python
router = FlaskRouter(
    app=app,
    title="My API",
    version="1.0.0",
    security_scheme=SecuritySchemeType.BEARER_JWT
)
```

### Custom Security Scheme

```python
router = FlaskRouter(
    app=app,
    title="My API",
    version="1.0.0",
    security_scheme={
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Enter your JWT token"
    }
)
```

### OAuth2

```python
router = FlaskRouter(
    app=app,
    security_scheme={
        "type": "oauth2",
        "flows": {
            "authorizationCode": {
                "authorizationUrl": "https://example.com/oauth/authorize",
                "tokenUrl": "https://example.com/oauth/token",
                "scopes": {
                    "read": "Read access",
                    "write": "Write access",
                    "admin": "Admin access"
                }
            }
        }
    }
)
```

## Additional OpenAPI Fields

The following OpenAPI fields are not supported as constructor parameters, but can be added manually via schema customization:

- **servers** - Server URLs for different environments
- **externalDocs** - Link to external documentation
- **info.contact** - API contact information
- **info.license** - API license information
- **info.termsOfService** - Terms of service URL
- **tags** - Tag metadata with descriptions

See [Custom Schema Generation](#custom-schema-generation) below for how to add these.

## Custom Schema Generation

### Override the openapi Property

The `openapi` property generates the schema lazily and caches it. You can override it to customize the schema:

```python
class MyRouter(FlaskRouter):
    @property
    def openapi(self) -> dict:
        """Get customized OpenAPI schema"""
        if self._openapi_schema is None:
            # Generate base schema
            from fastopenapi.openapi.generator import OpenAPIGenerator
            generator = OpenAPIGenerator(self)
            self._openapi_schema = generator.generate()

            # Add custom fields
            self._openapi_schema["x-api-id"] = "my-api"
            self._openapi_schema["x-custom-field"] = "custom-value"

            # Modify paths
            for path in self._openapi_schema["paths"].values():
                for operation in path.values():
                    if isinstance(operation, dict):
                        operation["x-code-samples"] = [
                            {
                                "lang": "Python",
                                "source": "# Python code here"
                            }
                        ]

        return self._openapi_schema
```

### Add Custom Components

```python
class MyRouter(FlaskRouter):
    @property
    def openapi(self) -> dict:
        if self._openapi_schema is None:
            from fastopenapi.openapi.generator import OpenAPIGenerator
            generator = OpenAPIGenerator(self)
            self._openapi_schema = generator.generate()

            # Add custom schemas
            self._openapi_schema["components"]["schemas"]["Error"] = {
                "type": "object",
                "properties": {
                    "code": {"type": "integer"},
                    "message": {"type": "string"}
                }
            }

            # Add response definitions
            self._openapi_schema["components"]["responses"] = {
                "NotFound": {
                    "description": "Resource not found",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"}
                        }
                    }
                }
            }

        return self._openapi_schema
```

## Model Schema Customization

### Field Customization

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    id: int = Field(..., description="User ID", example=1)
    username: str = Field(
        ...,
        description="Unique username",
        example="johndoe",
        min_length=3,
        max_length=50
    )
    email: EmailStr = Field(..., description="User email address")
    
    model_config = {
        "json_schema_extra": {
            "title": "User Model",
            "description": "Represents a user in the system"
        }
    }
```

### Exclude Fields from Schema

```python
class UserInternal(BaseModel):
    id: int
    username: str
    password_hash: str = Field(exclude=True)  # Not in OpenAPI schema
```

### Custom JSON Schema

```python
class User(BaseModel):
    id: int
    name: str
    
    @classmethod
    def model_json_schema(cls, **kwargs):
        schema = super().model_json_schema(**kwargs)
        # Customize schema
        schema["title"] = "User Object"
        schema["x-custom"] = "value"
        return schema
```

## Documentation UI Customization

### Disable Documentation

To disable all documentation endpoints, set any URL to `None`:

```python
router = FlaskRouter(
    app=app,
    docs_url=None,      # Disables all: Swagger UI, ReDoc, and OpenAPI JSON
)
```

### Custom Documentation Paths

```python
router = FlaskRouter(
    app=app,
    docs_url="/api-docs",           # Custom Swagger UI path
    redoc_url="/api-documentation", # Custom ReDoc path
    openapi_url="/api-schema.json"  # Custom schema path
)
```

## Complete Example

```python
from flask import Flask
from pydantic import BaseModel, EmailStr, Field
from fastopenapi.routers import FlaskRouter
from fastopenapi import Path, Query

app = Flask(__name__)

router = FlaskRouter(
    app=app,
    title="User Management API",
    version="2.0.0",
    description="""
    # User Management System

    This API provides endpoints for managing users in the system.

    ## Features

    * Create, read, update, and delete users
    * Search and filter users
    * User authentication
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

class UserCreate(BaseModel):
    username: str = Field(
        ...,
        description="Unique username",
        example="johndoe",
        min_length=3,
        max_length=50
    )
    email: EmailStr = Field(..., example="john@example.com")
    full_name: str = Field(..., example="John Doe")

class UserResponse(BaseModel):
    id: int = Field(..., description="User ID", example=1)
    username: str
    email: EmailStr
    full_name: str

@router.get(
    "/users",
    response_model=list[UserResponse],
    tags=["Users"],
    summary="List all users",
    description="Retrieve a paginated list of all users",
    responses={
        200: {"description": "Successful response"},
        500: {"description": "Internal server error"}
    }
)
def list_users(
    page: int = Query(1, description="Page number", ge=1),
    limit: int = Query(10, description="Items per page", ge=1, le=100)
):
    """List users with pagination."""
    return []

@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    tags=["Users"],
    summary="Get user by ID",
    responses={
        200: {"description": "User found"},
        404: {"description": "User not found"}
    }
)
def get_user(
    user_id: int = Path(..., description="User ID", example=1, ge=1)
):
    """Retrieve a single user by ID."""
    return UserResponse(
        id=user_id,
        username="johndoe",
        email="john@example.com",
        full_name="John Doe"
    )

@router.post(
    "/users",
    response_model=UserResponse,
    status_code=201,
    tags=["Users"],
    summary="Create new user",
    responses={
        201: {"description": "User created successfully"},
        400: {"description": "Invalid input"}
    }
)
def create_user(user: UserCreate):
    """Create a new user."""
    return UserResponse(id=1, **user.model_dump())

if __name__ == "__main__":
    print("API Documentation: http://localhost:5000/docs")
    app.run(debug=True)
```

## Next Steps

- [Architecture](architecture.md) - Understand schema generation
- [Custom Routers](custom_routers.md) - Extend schema generation
- [Testing](testing.md) - Test your API schema
