# Security

This guide covers authentication and authorization in FastOpenAPI.

## Security Schemes

FastOpenAPI supports multiple security schemes out of the box.

### Configuring Security

Set the security scheme when creating the router:

```python
from fastopenapi.routers import FlaskRouter
from fastopenapi import SecuritySchemeType

router = FlaskRouter(
    app=app,
    security_scheme=SecuritySchemeType.BEARER_JWT
)
```

### Available Security Schemes

- `BEARER_JWT` - Bearer token with JWT (default)
- `API_KEY_HEADER` - API key in header
- `API_KEY_QUERY` - API key in query parameter
- `BASIC_AUTH` - Basic authentication
- `OAUTH2` - OAuth2 flows

## Understanding Security()

The `Security()` class is a specialized dependency marker for authentication. It works like `Depends()` but additionally marks the endpoint as requiring authentication in the OpenAPI documentation.

### Basic Usage

`Security()` takes a dependency function that handles your authentication logic:

```python
from fastopenapi import Security, Depends, Header
from fastopenapi.errors import AuthenticationError

def get_bearer_token(authorization: str = Header(..., alias="Authorization")):
    if not authorization.startswith("Bearer "):
        raise AuthenticationError("Invalid authorization header")
    return authorization[7:]  # Token without "Bearer " prefix

@router.get("/protected")
def protected(token: str = Security(get_bearer_token)):
    payload = verify_jwt_token(token)
    return {"user_id": payload["user_id"]}
```

### Chaining Dependencies

You can build authentication chains using `Depends()` and `Security()`:

```python
def get_current_user(token: str = Depends(get_bearer_token)):
    payload = verify_jwt_token(token)
    user = database.get_user(payload["user_id"])
    if not user:
        raise AuthenticationError("User not found")
    return user

@router.get("/profile")
def profile(user = Security(get_current_user)):
    return {"username": user.username}
```

### Security() With Scopes

The `scopes` parameter allows OAuth2-style scope validation. Required scopes are injected into the dependency function via the `SecurityScopes` parameter:

```python
from fastopenapi import Security, SecurityScopes, Depends
from fastopenapi.errors import AuthorizationError

def verify_scopes(
    security_scopes: SecurityScopes,
    token: str = Depends(get_bearer_token),
):
    payload = verify_jwt_token(token)
    token_scopes = payload.get("scopes", [])

    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise AuthorizationError(f"Scope '{scope}' required")

    return payload

# Require specific scopes
@router.get("/admin/users")
def list_users(user = Security(verify_scopes, scopes=["admin:read"])):
    return {"users": [...]}

@router.delete("/users/{user_id}")
def delete_user(user_id: int, user = Security(verify_scopes, scopes=["users:delete"])):
    return {"deleted": user_id}
```

The `SecurityScopes` object receives the `scopes` list from the `Security()` declaration. The function itself decides how to validate them. Scopes are also shown in the OpenAPI documentation.

## Bearer JWT Authentication

### Basic Setup

```python
from fastopenapi import Security

router = FlaskRouter(
    app=app,
    security_scheme=SecuritySchemeType.BEARER_JWT
)

@router.get("/protected")
def protected_endpoint(token: str = Security(get_bearer_token)):
    payload = verify_jwt_token(token)
    return {"user_id": payload["user_id"]}
```

### JWT Token Validation

```python
import jwt
from datetime import datetime, timedelta
from fastopenapi.errors import AuthenticationError

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

def create_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token")
```

### Login Endpoint

```python
from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/login", response_model=LoginResponse)
def login(credentials: LoginRequest):
    user = authenticate_user(credentials.username, credentials.password)
    if not user:
        raise AuthenticationError("Invalid credentials")
    
    token = create_token(user.id)
    return {"access_token": token, "token_type": "bearer"}
```

### Protected Endpoints with JWT

```python
def get_current_user(token: str = Depends(get_bearer_token)):
    payload = verify_jwt_token(token)
    user = database.get_user(payload["user_id"])
    if not user:
        raise AuthenticationError("User not found")
    return user

@router.get("/profile")
def get_profile(current_user = Depends(get_current_user)):
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "email": current_user.email
    }
```

## API Key Authentication

### Header-Based API Key

```python
router = FlaskRouter(
    app=app,
    security_scheme=SecuritySchemeType.API_KEY_HEADER
)

VALID_API_KEYS = {
    "key123": {"user_id": 1, "name": "User 1"},
    "key456": {"user_id": 2, "name": "User 2"}
}

def verify_api_key(api_key: str = Header(..., alias="X-API-Key")):
    if api_key not in VALID_API_KEYS:
        raise AuthenticationError("Invalid API key")
    return VALID_API_KEYS[api_key]

@router.get("/data")
def get_data(user_data = Depends(verify_api_key)):
    return {"data": "sensitive", "user": user_data["name"]}
```

### Query Parameter API Key

```python
router = FlaskRouter(
    app=app,
    security_scheme=SecuritySchemeType.API_KEY_QUERY
)

def verify_api_key(api_key: str = Query(...)):
    if api_key not in VALID_API_KEYS:
        raise AuthenticationError("Invalid API key")
    return VALID_API_KEYS[api_key]

@router.get("/data")
def get_data(user_data = Depends(verify_api_key)):
    return {"data": "sensitive"}
```

## Basic Authentication

### Setup

```python
import base64
from fastopenapi import Header

router = FlaskRouter(
    app=app,
    security_scheme=SecuritySchemeType.BASIC_AUTH
)

def verify_basic_auth(authorization: str = Header(..., alias="Authorization")):
    if not authorization.startswith("Basic "):
        raise AuthenticationError("Invalid authorization header")
    
    # Decode base64
    encoded = authorization[6:]
    try:
        decoded = base64.b64decode(encoded).decode("utf-8")
        username, password = decoded.split(":", 1)
    except Exception:
        raise AuthenticationError("Invalid authorization format")
    
    # Verify credentials
    user = authenticate_user(username, password)
    if not user:
        raise AuthenticationError("Invalid credentials")
    
    return user

@router.get("/protected")
def protected_endpoint(user = Depends(verify_basic_auth)):
    return {"message": f"Hello, {user.username}"}
```

## OAuth2

### OAuth2 Password Flow

```python
from pydantic import BaseModel

router = FlaskRouter(
    app=app,
    security_scheme=SecuritySchemeType.OAUTH2
)

class OAuth2TokenRequest(BaseModel):
    grant_type: str
    username: str
    password: str
    scope: str = ""

class OAuth2TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    scope: str

@router.post("/token", response_model=OAuth2TokenResponse)
def get_token(form_data: OAuth2TokenRequest = Form(...)):
    if form_data.grant_type != "password":
        raise BadRequestError("Unsupported grant type")
    
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise AuthenticationError("Invalid credentials")
    
    token = create_token(user.id)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 86400,
        "scope": form_data.scope
    }
```

## Role-Based Access Control

### Simple Role Check

```python
class User:
    def __init__(self, id: int, username: str, role: str):
        self.id = id
        self.username = username
        self.role = role

def get_current_user(token: str = Depends(get_bearer_token)) -> User:
    payload = verify_jwt_token(token)
    user = database.get_user(payload["user_id"])
    return user

def require_role(role: str):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != role:
            raise AuthorizationError(f"Role '{role}' required")
        return current_user
    return role_checker

@router.get("/admin/users")
def list_all_users(admin: User = Depends(require_role("admin"))):
    return {"users": database.get_all_users()}
```

### Multiple Roles

```python
def require_any_role(*roles: str):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise AuthorizationError(f"One of roles {roles} required")
        return current_user
    return role_checker

@router.get("/moderator/reports")
def get_reports(user: User = Depends(require_any_role("admin", "moderator"))):
    return {"reports": get_pending_reports()}
```

## Permission-Based Access Control

### Permission System

```python
class User:
    def __init__(self, id: int, username: str, permissions: list[str]):
        self.id = id
        self.username = username
        self.permissions = permissions
    
    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

def require_permission(permission: str):
    def permission_checker(current_user: User = Depends(get_current_user)):
        if not current_user.has_permission(permission):
            raise AuthorizationError(f"Permission '{permission}' required")
        return current_user
    return permission_checker

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(require_permission("users:delete"))
):
    database.delete_user(user_id)
    return {"deleted": user_id}
```

### Hierarchical Permissions

```python
PERMISSION_HIERARCHY = {
    "admin": ["users:read", "users:write", "users:delete", "posts:*"],
    "editor": ["posts:read", "posts:write"],
    "viewer": ["posts:read"]
}

def expand_permissions(role: str) -> set[str]:
    perms = set()
    for perm in PERMISSION_HIERARCHY.get(role, []):
        if perm.endswith(":*"):
            # Wildcard permission
            prefix = perm[:-1]
            perms.update([p for p in ALL_PERMISSIONS if p.startswith(prefix)])
        else:
            perms.add(perm)
    return perms

def check_permission(user: User, required: str) -> bool:
    user_perms = expand_permissions(user.role)
    return required in user_perms
```

## Resource Ownership

### Owner-Only Access

```python
def require_owner(resource_type: str):
    def ownership_checker(
        resource_id: int,
        current_user: User = Depends(get_current_user)
    ):
        resource = database.get_resource(resource_type, resource_id)
        if not resource:
            raise ResourceNotFoundError(f"{resource_type} not found")
        
        if resource.owner_id != current_user.id and current_user.role != "admin":
            raise AuthorizationError("You don't own this resource")
        
        return resource
    return ownership_checker

@router.put("/posts/{post_id}")
def update_post(
    post_id: int,
    updates: PostUpdate,
    post = Depends(require_owner("post"))
):
    database.update_post(post_id, updates)
    return {"updated": post_id}
```

## Scopes

### Token with Scopes

```python
def create_token_with_scopes(user_id: int, scopes: list[str]) -> str:
    payload = {
        "user_id": user_id,
        "scopes": scopes,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_scopes(
    security_scopes: SecurityScopes,
    token: str = Depends(get_bearer_token),
):
    payload = verify_jwt_token(token)
    token_scopes = set(payload.get("scopes", []))

    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise AuthorizationError(f"Scope '{scope}' required")

    return payload

@router.get("/admin/stats")
def admin_stats(payload = Security(verify_scopes, scopes=["admin:read", "stats:read"])):
    return {"stats": get_statistics()}
```

## Rate Limiting

### Simple Rate Limiter

```python
from datetime import datetime, timedelta
from collections import defaultdict

rate_limits = defaultdict(list)

def rate_limit(max_requests: int = 100, window_seconds: int = 3600):
    def limiter(
        api_key: str = Header(..., alias="X-API-Key")
    ):
        now = datetime.utcnow()
        key = f"rate:{api_key}"
        
        # Clean old requests
        rate_limits[key] = [
            req_time for req_time in rate_limits[key]
            if now - req_time < timedelta(seconds=window_seconds)
        ]
        
        # Check limit
        if len(rate_limits[key]) >= max_requests:
            raise AuthorizationError("Rate limit exceeded")
        
        # Record request
        rate_limits[key].append(now)
        return api_key
    
    return limiter

@router.get("/api/data")
def get_data(api_key: str = Depends(rate_limit(max_requests=100))):
    return {"data": "..."}
```

### User-Based Rate Limiting

```python
def user_rate_limit(max_requests: int = 100):
    def limiter(current_user: User = Depends(get_current_user)):
        now = datetime.utcnow()
        key = f"rate:user:{current_user.id}"
        
        rate_limits[key] = [
            req_time for req_time in rate_limits[key]
            if now - req_time < timedelta(hours=1)
        ]
        
        if len(rate_limits[key]) >= max_requests:
            raise AuthorizationError("Rate limit exceeded")
        
        rate_limits[key].append(now)
        return current_user
    
    return limiter

@router.get("/expensive-operation")
def expensive_op(user: User = Depends(user_rate_limit(max_requests=10))):
    return perform_expensive_operation()
```

## IP Whitelisting

### IP-Based Access Control

```python
from fastopenapi import Header, Depends
from fastopenapi.errors import AuthorizationError

ALLOWED_IPS = {"192.168.1.1", "10.0.0.1"}

def require_whitelisted_ip(
    x_forwarded_for: str = Header(..., alias="X-Forwarded-For"),
):
    if x_forwarded_for not in ALLOWED_IPS:
        raise AuthorizationError("Access denied from this IP")
    return x_forwarded_for

@router.get("/internal/status")
def internal_status(client_ip: str = Depends(require_whitelisted_ip)):
    return {"status": "ok", "client_ip": client_ip}
```

## Multi-Factor Authentication

### TOTP Verification

```python
import pyotp

def verify_totp(
    totp_code: str = Header(..., alias="X-TOTP-Code"),
    current_user: User = Depends(get_current_user)
):
    totp = pyotp.TOTP(current_user.totp_secret)
    
    if not totp.verify(totp_code):
        raise AuthenticationError("Invalid TOTP code")
    
    return current_user

@router.get("/sensitive-data")
def get_sensitive_data(user: User = Depends(verify_totp)):
    return {"data": "highly sensitive"}
```

## Security Headers

### Adding Security Headers

```python
from fastopenapi import Response

@router.get("/secure-endpoint")
def secure_endpoint():
    return Response(
        content={"data": "secure"},
        headers={
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
        }
    )
```

## CORS Configuration

### Framework-Specific CORS

For production, use framework-specific CORS middleware:

**Flask:**
```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "https://example.com"}})
```

**Starlette:**
```python
from starlette.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

## Password Security

### Password Hashing

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str) -> User | None:
    user = database.get_user_by_username(username)
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user
```

## Session Management

### Session Tokens

```python
import secrets

sessions = {}  # Use Redis in production

def create_session(user_id: int) -> str:
    session_token = secrets.token_urlsafe(32)
    sessions[session_token] = {
        "user_id": user_id,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=24)
    }
    return session_token

def get_session_user(session_token: str = Cookie(...)):
    session = sessions.get(session_token)
    if not session:
        raise AuthenticationError("Invalid session")
    
    if datetime.utcnow() > session["expires_at"]:
        del sessions[session_token]
        raise AuthenticationError("Session expired")
    
    user = database.get_user(session["user_id"])
    return user

@router.get("/profile")
def get_profile(user: User = Depends(get_session_user)):
    return {"user": user}
```

## Security Best Practices

### 1. Never Store Plaintext Passwords

```python
# Good
user.hashed_password = hash_password(password)

# NEVER DO THIS
user.password = password
```

### 2. Use HTTPS in Production

Always use HTTPS for APIs handling authentication.

### 3. Validate Token Expiration

```python
# Good
if datetime.utcnow() > token_payload["exp"]:
    raise AuthenticationError("Token expired")

# Avoid - no expiration check
```

### 4. Use Strong Secret Keys

```python
# Good
SECRET_KEY = secrets.token_urlsafe(32)

# NEVER DO THIS
SECRET_KEY = "password123"
```

### 5. Implement Rate Limiting

Always implement rate limiting on authentication endpoints.

### 6. Log Security Events

```python
import logging

logger = logging.getLogger(__name__)

def authenticate_user(username: str, password: str):
    user = database.get_user_by_username(username)
    
    if not user or not verify_password(password, user.hashed_password):
        logger.warning(f"Failed login attempt for user: {username}")
        return None
    
    logger.info(f"Successful login for user: {username}")
    return user
```

### 7. Use Secure Token Storage

Store JWT secret keys in environment variables:

```python
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY environment variable not set")
```

## Common Security Patterns

### Refresh Tokens

```python
def create_tokens(user_id: int):
    access_token = create_token(user_id, expires_delta=timedelta(minutes=15))
    refresh_token = create_token(user_id, expires_delta=timedelta(days=30))
    return access_token, refresh_token

@router.post("/refresh")
def refresh_access_token(refresh_token: str = Body(...)):
    try:
        payload = verify_jwt_token(refresh_token)
        new_access_token = create_token(payload["user_id"])
        return {"access_token": new_access_token}
    except Exception:
        raise AuthenticationError("Invalid refresh token")
```

### Password Reset

```python
def create_reset_token(email: str) -> str:
    token = secrets.token_urlsafe(32)
    reset_tokens[token] = {
        "email": email,
        "expires_at": datetime.utcnow() + timedelta(hours=1)
    }
    return token

@router.post("/password-reset-request")
def request_password_reset(email: str = Body(...)):
    user = database.get_user_by_email(email)
    if user:
        token = create_reset_token(email)
        send_reset_email(email, token)
    
    # Always return success to prevent email enumeration
    return {"message": "If account exists, reset email sent"}

@router.post("/password-reset")
def reset_password(token: str = Body(...), new_password: str = Body(...)):
    reset_data = reset_tokens.get(token)
    
    if not reset_data or datetime.utcnow() > reset_data["expires_at"]:
        raise AuthenticationError("Invalid or expired reset token")
    
    user = database.get_user_by_email(reset_data["email"])
    user.hashed_password = hash_password(new_password)
    database.save(user)
    
    del reset_tokens[token]
    return {"message": "Password reset successful"}
```

## Next Steps

- [Error Handling](error_handling.md) - Handle authentication errors
- [Dependencies](dependencies.md) - More on dependency injection
- [Examples](../examples/authentication.md) - Complete auth example
- [Testing](../advanced/testing.md) - Test secured endpoints
