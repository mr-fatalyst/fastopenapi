# Authentication Example

This example demonstrates different authentication strategies in FastOpenAPI.

## Bearer Token Authentication

### Basic Implementation

```python
from flask import Flask
from pydantic import BaseModel
from datetime import datetime, timedelta
import secrets
import hashlib
from fastopenapi import Header, Depends, Security
from fastopenapi.routers import FlaskRouter
from fastopenapi.errors import AuthenticationError, ResourceConflictError

app = Flask(__name__)
router = FlaskRouter(
    app=app,
    title="Auth API",
    version="1.0.0"
)

# In-memory storage
users_db = {}
sessions_db = {}

# Configuration
SECRET_KEY = "your-secret-key-change-in-production"
TOKEN_EXPIRY = timedelta(hours=24)

class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_session(user_id: int) -> str:
    """Create authentication session"""
    token = secrets.token_urlsafe(32)
    sessions_db[token] = {
        "user_id": user_id,
        "created_at": datetime.now(),
        "expires_at": datetime.now() + TOKEN_EXPIRY
    }
    return token

def get_current_user(
    authorization: str = Header(..., alias="Authorization")
):
    """Dependency to get current authenticated user"""
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError("Invalid authorization header")

    token = authorization.replace("Bearer ", "")
    session = sessions_db.get(token)

    if not session:
        raise AuthenticationError("Invalid token")

    if session["expires_at"] < datetime.now():
        del sessions_db[token]
        raise AuthenticationError("Token expired")

    user = users_db.get(session["user_id"])
    if not user:
        raise AuthenticationError("User not found")

    return user

# Public endpoints

@router.post("/auth/register", response_model=UserResponse, status_code=201)
def register(user: UserRegister):
    """Register a new user"""
    # Check if user exists
    for u in users_db.values():
        if u["username"] == user.username:
            raise ResourceConflictError("Username already exists")
        if u["email"] == user.email:
            raise ResourceConflictError("Email already registered")

    # Create user
    user_id = len(users_db) + 1
    users_db[user_id] = {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "password_hash": hash_password(user.password)
    }

    return UserResponse(
        id=user_id,
        username=user.username,
        email=user.email
    )

@router.post("/auth/login")
def login(credentials: UserLogin):
    """Login and get access token"""
    # Find user
    user = None
    for u in users_db.values():
        if u["username"] == credentials.username:
            user = u
            break

    if not user:
        raise AuthenticationError("Invalid credentials")

    # Verify password
    if user["password_hash"] != hash_password(credentials.password):
        raise AuthenticationError("Invalid credentials")

    # Create session
    token = create_session(user["id"])

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": TOKEN_EXPIRY.total_seconds()
    }

@router.post("/auth/logout")
def logout(user = Depends(get_current_user)):
    """Logout (invalidate current token)"""
    # In real implementation, remove token from sessions
    return {"message": "Logged out successfully"}

# Protected endpoints

@router.get("/users/me", response_model=UserResponse)
def get_my_profile(user = Depends(get_current_user)):
    """Get current user profile"""
    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"]
    )

@router.get("/protected")
def protected_endpoint(user = Depends(get_current_user)):
    """Example protected endpoint"""
    return {
        "message": f"Hello, {user['username']}!",
        "user_id": user["id"]
    }

if __name__ == "__main__":
    app.run(debug=True)
```

### Testing

```bash
# Register a user
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "email": "john@example.com", "password": "secret123"}'

# Login
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "password": "secret123"}'
# Returns: {"access_token": "...", "token_type": "bearer", "expires_in": 86400}

# Access protected endpoint
curl http://localhost:5000/users/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Logout
curl -X POST http://localhost:5000/auth/logout \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## API Key Authentication

```python
from fastopenapi import Header
from fastopenapi.errors import AuthenticationError

# Valid API keys (in production, store in database)
API_KEYS = {
    "key_abc123": {"user_id": 1, "name": "Service A"},
    "key_xyz789": {"user_id": 2, "name": "Service B"}
}

def verify_api_key(
    api_key: str = Header(..., alias="X-API-Key")
):
    """Verify API key"""
    if api_key not in API_KEYS:
        raise AuthenticationError("Invalid API key")

    return API_KEYS[api_key]

@router.get("/api/data")
def get_data(client = Depends(verify_api_key)):
    """Endpoint protected by API key"""
    return {
        "data": "sensitive data",
        "client": client["name"]
    }
```

### Testing

```bash
curl http://localhost:5000/api/data \
  -H "X-API-Key: key_abc123"
```

---

## JWT Authentication

```python
import jwt
from datetime import datetime, timedelta
from fastopenapi import Header
from fastopenapi.errors import AuthenticationError

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    """Create JWT token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user_jwt(
    authorization: str = Header(..., alias="Authorization")
):
    """Get current user from JWT token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError("Invalid authorization header")

    token = authorization.replace("Bearer ", "")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise AuthenticationError("Invalid token payload")
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token expired")
    except jwt.JWTError:
        raise AuthenticationError("Invalid token")

    # Get user from database
    user = users_db.get(int(user_id))
    if not user:
        raise AuthenticationError("User not found")

    return user

@router.post("/auth/jwt/login")
def jwt_login(credentials: UserLogin):
    """Login with JWT"""
    # Verify credentials (same as before)
    user = None
    for u in users_db.values():
        if u["username"] == credentials.username:
            user = u
            break

    if not user or user["password_hash"] != hash_password(credentials.password):
        raise AuthenticationError("Invalid credentials")

    # Create JWT token
    access_token = create_access_token({"sub": str(user["id"])})

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/jwt/protected")
def jwt_protected(user = Depends(get_current_user_jwt)):
    """JWT protected endpoint"""
    return {"message": f"Hello, {user['username']}!"}
```

---

## Role-Based Access Control (RBAC)

```python
from enum import Enum
from fastopenapi.errors import AuthorizationError, ResourceNotFoundError

class UserRole(str, Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"

# Add roles to users
def create_user_with_role(username, email, password, role=UserRole.USER):
    user_id = len(users_db) + 1
    users_db[user_id] = {
        "id": user_id,
        "username": username,
        "email": email,
        "password_hash": hash_password(password),
        "role": role
    }
    return user_id

def require_role(required_role: UserRole):
    """Dependency factory for role-based access"""
    def role_checker(user = Depends(get_current_user)):
        if user["role"] != required_role:
            raise AuthorizationError(f"Role '{required_role}' required")
        return user
    return role_checker

def require_admin(user = Depends(get_current_user)):
    """Require admin role"""
    if user["role"] != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    return user

@router.get("/admin/users")
def list_all_users(admin = Depends(require_admin)):
    """Admin endpoint to list all users"""
    return [
        {"id": u["id"], "username": u["username"], "role": u["role"]}
        for u in users_db.values()
    ]

@router.delete("/admin/users/{user_id}")
def delete_user(
    user_id: int,
    admin = Depends(require_admin)
):
    """Admin endpoint to delete users"""
    if user_id not in users_db:
        raise ResourceNotFoundError("User not found")

    if user_id == admin["id"]:
        raise AuthorizationError("Cannot delete yourself")

    del users_db[user_id]
    return {"message": "User deleted"}

@router.get("/moderator/posts")
def moderate_posts(moderator = Depends(require_role(UserRole.MODERATOR))):
    """Moderator endpoint"""
    return {"message": "Moderator access granted"}
```

---

## OAuth2 with Scopes

```python
from fastopenapi import Security, SecurityScopes

def verify_token_scopes(
    authorization: str = Header(..., alias="Authorization"),
    security_scopes: SecurityScopes,
):
    """Verify token and check scopes"""
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError("Invalid authorization header")

    token = authorization.replace("Bearer ", "")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        token_scopes = payload.get("scopes", [])
    except jwt.JWTError:
        raise AuthenticationError("Invalid token")

    # Check if token has required scopes
    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise AuthenticationError(f"Scope '{scope}' required")

    user = users_db.get(int(user_id))
    if not user:
        raise AuthenticationError("User not found")

    return user

@router.get("/admin/settings")
def admin_settings(
    user = Security(verify_token_scopes, scopes=["admin:read"])
):
    """Requires 'admin:read' scope"""
    return {"settings": "..."}

@router.post("/admin/settings")
def update_admin_settings(
    settings: dict,
    user = Security(verify_token_scopes, scopes=["admin:write"])
):
    """Requires 'admin:write' scope"""
    return {"message": "Settings updated"}

@router.delete("/users/{user_id}")
def delete_user_oauth(
    user_id: int,
    user = Security(verify_token_scopes, scopes=["users:delete"])
):
    """Requires 'users:delete' scope"""
    return {"message": "User deleted"}
```

---

## Optional Authentication

```python
def get_optional_user(
    authorization: str = Header(None, alias="Authorization")
):
    """Get user if authenticated, None otherwise"""
    if not authorization or not authorization.startswith("Bearer "):
        return None

    try:
        return get_current_user(authorization)
    except:
        return None

@router.get("/posts")
def list_posts(user = Depends(get_optional_user)):
    """Endpoint with optional authentication"""
    if user:
        # Return personalized results
        return {
            "posts": "personalized for " + user["username"],
            "recommendations": True
        }
    else:
        # Return public results
        return {
            "posts": "public posts",
            "recommendations": False
        }
```

---

## Multi-Factor Authentication (MFA)

```python
import pyotp

# Store MFA secrets in user records
def enable_mfa(user = Depends(get_current_user)):
    """Enable MFA for current user"""
    # Generate secret
    secret = pyotp.random_base32()

    # Store secret for user
    users_db[user["id"]]["mfa_secret"] = secret

    # Generate QR code URI
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=user["email"],
        issuer_name="My App"
    )

    return {
        "secret": secret,
        "provisioning_uri": provisioning_uri,
        "qr_code": provisioning_uri  # Use QR code library to generate image
    }

class MFAVerify(BaseModel):
    code: str

@router.post("/auth/mfa/verify")
def verify_mfa(
    mfa: MFAVerify,
    user = Depends(get_current_user)
):
    """Verify MFA code"""
    if "mfa_secret" not in users_db[user["id"]]:
        raise AuthenticationError("MFA not enabled")

    secret = users_db[user["id"]]["mfa_secret"]
    totp = pyotp.TOTP(secret)

    if not totp.verify(mfa.code):
        raise AuthenticationError("Invalid MFA code")

    return {"message": "MFA verified"}
```

---

## Session Management

```python
from datetime import datetime

class SessionManager:
    """Manage user sessions"""

    def __init__(self):
        self.sessions = {}

    def create_session(self, user_id: int, remember_me: bool = False):
        """Create new session"""
        token = secrets.token_urlsafe(32)
        expiry = timedelta(hours=24 if not remember_me else 720)  # 30 days

        self.sessions[token] = {
            "user_id": user_id,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + expiry,
            "last_activity": datetime.now()
        }

        return token

    def get_session(self, token: str):
        """Get session if valid"""
        session = self.sessions.get(token)

        if not session:
            return None

        if session["expires_at"] < datetime.now():
            del self.sessions[token]
            return None

        # Update last activity
        session["last_activity"] = datetime.now()

        return session

    def delete_session(self, token: str):
        """Delete session (logout)"""
        if token in self.sessions:
            del self.sessions[token]

    def delete_user_sessions(self, user_id: int):
        """Delete all sessions for a user"""
        to_delete = [
            token for token, session in self.sessions.items()
            if session["user_id"] == user_id
        ]

        for token in to_delete:
            del self.sessions[token]

session_manager = SessionManager()

@router.post("/auth/logout-all")
def logout_all_sessions(user = Depends(get_current_user)):
    """Logout from all devices"""
    session_manager.delete_user_sessions(user["id"])
    return {"message": "Logged out from all devices"}

@router.get("/auth/sessions")
def list_sessions(user = Depends(get_current_user)):
    """List all active sessions"""
    user_sessions = [
        {
            "created_at": session["created_at"],
            "last_activity": session["last_activity"],
            "expires_at": session["expires_at"]
        }
        for session in session_manager.sessions.values()
        if session["user_id"] == user["id"]
    ]

    return {"sessions": user_sessions}
```

---

## Best Practices

### 1. Never Store Plain Passwords

```python
# Good
password_hash = hashlib.sha256(password.encode()).hexdigest()

# Better - use bcrypt
import bcrypt
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
```

### 2. Use Secure Token Generation

```python
# Good
import secrets
token = secrets.token_urlsafe(32)

# Avoid
import random
token = str(random.randint(1000, 9999))  # Not secure!
```

### 3. Set Token Expiry

```python
# Good
expires_at = datetime.now() + timedelta(hours=24)

# Avoid
# No expiry - tokens valid forever
```

### 4. Validate Token on Every Request

```python
# Good
if session["expires_at"] < datetime.now():
    del sessions_db[token]
    raise AuthenticationError("Token expired")

# Avoid
# Not checking expiry
```

### 5. Use HTTPS in Production

Always use HTTPS to protect tokens in transit.

---

## See Also

- [Security Guide](../guide/security.md) - Security best practices
- [Dependencies Reference](../api_reference/dependencies.md) - Using Depends and Security
- [Error Handling](../guide/error_handling.md) - Authentication errors
