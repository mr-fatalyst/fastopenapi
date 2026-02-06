# CRUD API Example

This example demonstrates building a complete CRUD (Create, Read, Update, Delete) API for managing users using FastOpenAPI.

## Complete Example

```python
from flask import Flask
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
from fastopenapi.routers import FlaskRouter
from fastopenapi.errors import ResourceNotFoundError, BadRequestError
from fastopenapi import Query

app = Flask(__name__)
router = FlaskRouter(
    app=app,
    title="User Management API",
    version="1.0.0",
    description="Complete CRUD API for user management"
)

# In-memory database
users_db = {}
next_id = 1

# Models
class UserBase(BaseModel):
    """Base user model with common fields"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=100)
    is_active: bool = True

class UserCreate(UserBase):
    """Model for creating a new user"""
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    """Model for updating user (all fields optional)"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    """Model for user responses"""
    id: int
    created_at: datetime
    updated_at: datetime

class UserListResponse(BaseModel):
    """Paginated list of users"""
    users: list[UserResponse]
    total: int
    page: int
    per_page: int
    total_pages: int

# Helper functions
def hash_password(password: str) -> str:
    """Hash password (simplified - use bcrypt in production)"""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_by_id(user_id: int) -> Optional[dict]:
    """Get user by ID"""
    return users_db.get(user_id)

def get_user_by_username(username: str) -> Optional[dict]:
    """Get user by username"""
    for user in users_db.values():
        if user["username"] == username:
            return user
    return None

def get_user_by_email(email: str) -> Optional[dict]:
    """Get user by email"""
    for user in users_db.values():
        if user["email"] == email:
            return user
    return None

# Endpoints

@router.get("/", tags=["Root"])
def root():
    """API root endpoint"""
    return {
        "message": "User Management API",
        "version": "1.0.0",
        "endpoints": {
            "users": "/users",
            "docs": "/docs",
            "openapi": "/openapi.json"
        }
    }

@router.get(
    "/users",
    response_model=UserListResponse,
    tags=["Users"],
    summary="List all users",
    description="Get a paginated list of all users"
)
def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Users per page"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in username or email")
):
    """
    List all users with pagination and optional filtering.
    
    - **page**: Page number (starts from 1)
    - **per_page**: Number of users per page (max 100)
    - **is_active**: Filter by active status
    - **search**: Search in username or email
    """
    # Get all users
    users = list(users_db.values())
    
    # Filter by active status
    if is_active is not None:
        users = [u for u in users if u["is_active"] == is_active]
    
    # Search filter
    if search:
        search_lower = search.lower()
        users = [
            u for u in users
            if search_lower in u["username"].lower()
            or search_lower in u["email"].lower()
        ]
    
    # Calculate pagination
    total = len(users)
    total_pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    
    # Get page of users
    page_users = users[start:end]
    
    return {
        "users": page_users,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages
    }

@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    tags=["Users"],
    summary="Get user by ID",
    description="Retrieve a single user by their ID"
)
def get_user(user_id: int):
    """
    Get a specific user by ID.
    
    - **user_id**: The ID of the user to retrieve
    """
    user = get_user_by_id(user_id)
    if not user:
        raise ResourceNotFoundError(f"User with ID {user_id} not found")
    return user

@router.post(
    "/users",
    response_model=UserResponse,
    status_code=201,
    tags=["Users"],
    summary="Create new user",
    description="Create a new user with the provided data"
)
def create_user(user: UserCreate):
    """
    Create a new user.
    
    - **username**: Unique username (3-50 characters)
    - **email**: Valid email address (must be unique)
    - **full_name**: Optional full name
    - **password**: Password (minimum 8 characters)
    - **is_active**: Whether the user is active (default: true)
    """
    global next_id
    
    # Check if username already exists
    if get_user_by_username(user.username):
        raise BadRequestError(f"Username '{user.username}' already exists")
    
    # Check if email already exists
    if get_user_by_email(user.email):
        raise BadRequestError(f"Email '{user.email}' already exists")
    
    # Create new user
    now = datetime.now()
    new_user = {
        "id": next_id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "password_hash": hash_password(user.password),  # Never store plain passwords
        "created_at": now,
        "updated_at": now
    }
    
    users_db[next_id] = new_user
    next_id += 1
    
    # Remove password_hash from response
    response_user = new_user.copy()
    del response_user["password_hash"]
    
    return response_user

@router.put(
    "/users/{user_id}",
    response_model=UserResponse,
    tags=["Users"],
    summary="Update user (full)",
    description="Replace all user data with new data"
)
def replace_user(user_id: int, user: UserCreate):
    """
    Replace entire user (PUT).
    
    All fields are required and will replace the existing user completely.
    """
    existing_user = get_user_by_id(user_id)
    if not existing_user:
        raise ResourceNotFoundError(f"User with ID {user_id} not found")
    
    # Check username uniqueness (excluding current user)
    existing_by_username = get_user_by_username(user.username)
    if existing_by_username and existing_by_username["id"] != user_id:
        raise BadRequestError(f"Username '{user.username}' already exists")
    
    # Check email uniqueness (excluding current user)
    existing_by_email = get_user_by_email(user.email)
    if existing_by_email and existing_by_email["id"] != user_id:
        raise BadRequestError(f"Email '{user.email}' already exists")
    
    # Update user
    updated_user = {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "password_hash": hash_password(user.password),
        "created_at": existing_user["created_at"],
        "updated_at": datetime.now()
    }
    
    users_db[user_id] = updated_user
    
    # Remove password_hash from response
    response_user = updated_user.copy()
    del response_user["password_hash"]
    
    return response_user

@router.patch(
    "/users/{user_id}",
    response_model=UserResponse,
    tags=["Users"],
    summary="Update user (partial)",
    description="Update only specified fields of a user"
)
def update_user(user_id: int, updates: UserUpdate):
    """
    Partially update a user (PATCH).
    
    Only provided fields will be updated. Other fields remain unchanged.
    """
    user = get_user_by_id(user_id)
    if not user:
        raise ResourceNotFoundError(f"User with ID {user_id} not found")
    
    # Get update data (exclude unset fields)
    update_data = updates.model_dump(exclude_unset=True)
    
    # Check username uniqueness if updating username
    if "username" in update_data:
        existing = get_user_by_username(update_data["username"])
        if existing and existing["id"] != user_id:
            raise BadRequestError(f"Username '{update_data['username']}' already exists")
    
    # Check email uniqueness if updating email
    if "email" in update_data:
        existing = get_user_by_email(update_data["email"])
        if existing and existing["id"] != user_id:
            raise BadRequestError(f"Email '{update_data['email']}' already exists")
    
    # Hash password if updating
    if "password" in update_data:
        update_data["password_hash"] = hash_password(update_data["password"])
        del update_data["password"]
    
    # Update user
    user.update(update_data)
    user["updated_at"] = datetime.now()
    users_db[user_id] = user
    
    # Remove password_hash from response
    response_user = user.copy()
    del response_user["password_hash"]
    
    return response_user

@router.delete(
    "/users/{user_id}",
    status_code=204,
    tags=["Users"],
    summary="Delete user",
    description="Permanently delete a user"
)
def delete_user(user_id: int):
    """
    Delete a user.
    
    This action cannot be undone.
    """
    if user_id not in users_db:
        raise ResourceNotFoundError(f"User with ID {user_id} not found")
    
    del users_db[user_id]
    return None

# Bulk operations

@router.post(
    "/users/bulk",
    response_model=dict,
    status_code=201,
    tags=["Bulk Operations"],
    summary="Create multiple users",
    description="Create multiple users in a single request"
)
def bulk_create_users(users: list[UserCreate]):
    """
    Create multiple users at once.
    
    Returns count of successfully created users and any errors.
    """
    global next_id
    
    created = []
    errors = []
    
    for idx, user in enumerate(users):
        try:
            # Check duplicates
            if get_user_by_username(user.username):
                errors.append({
                    "index": idx,
                    "error": f"Username '{user.username}' already exists"
                })
                continue
            
            if get_user_by_email(user.email):
                errors.append({
                    "index": idx,
                    "error": f"Email '{user.email}' already exists"
                })
                continue
            
            # Create user
            now = datetime.now()
            new_user = {
                "id": next_id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "password_hash": hash_password(user.password),
                "created_at": now,
                "updated_at": now
            }
            
            users_db[next_id] = new_user
            created.append(next_id)
            next_id += 1
            
        except Exception as e:
            errors.append({
                "index": idx,
                "error": str(e)
            })
    
    return {
        "created_count": len(created),
        "created_ids": created,
        "error_count": len(errors),
        "errors": errors
    }

@router.delete(
    "/users/bulk",
    status_code=200,
    tags=["Bulk Operations"],
    summary="Delete multiple users",
    description="Delete multiple users by their IDs"
)
def bulk_delete_users(user_ids: list[int]):
    """
    Delete multiple users at once.
    
    Returns count of deleted users and any errors.
    """
    deleted = []
    errors = []
    
    for user_id in user_ids:
        if user_id in users_db:
            del users_db[user_id]
            deleted.append(user_id)
        else:
            errors.append({
                "user_id": user_id,
                "error": "User not found"
            })
    
    return {
        "deleted_count": len(deleted),
        "deleted_ids": deleted,
        "error_count": len(errors),
        "errors": errors
    }

# Run the application
if __name__ == "__main__":
    # Add some sample users
    sample_users = [
        UserCreate(
            username="alice",
            email="alice@example.com",
            full_name="Alice Smith",
            password="password123"
        ),
        UserCreate(
            username="bob",
            email="bob@example.com",
            full_name="Bob Johnson",
            password="password123"
        ),
    ]
    
    for user in sample_users:
        create_user(user)
    
    print("Sample users created!")
    print("API running on http://localhost:5000")
    print("Docs at http://localhost:5000/docs")
    
    app.run(debug=True)
```

## Testing the API

### List Users
```bash
curl http://localhost:5000/users
curl http://localhost:5000/users?page=1&per_page=5
curl http://localhost:5000/users?is_active=true
curl http://localhost:5000/users?search=alice
```

### Get Single User
```bash
curl http://localhost:5000/users/1
```

### Create User
```bash
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "charlie",
    "email": "charlie@example.com",
    "full_name": "Charlie Brown",
    "password": "securepass123",
    "is_active": true
  }'
```

### Update User (Full)
```bash
curl -X PUT http://localhost:5000/users/1 \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice_updated",
    "email": "alice.new@example.com",
    "full_name": "Alice Updated",
    "password": "newpassword123",
    "is_active": true
  }'
```

### Update User (Partial)
```bash
curl -X PATCH http://localhost:5000/users/1 \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Alice Wilson"
  }'
```

### Delete User
```bash
curl -X DELETE http://localhost:5000/users/1
```

### Bulk Create
```bash
curl -X POST http://localhost:5000/users/bulk \
  -H "Content-Type: application/json" \
  -d '[
    {
      "username": "user1",
      "email": "user1@example.com",
      "password": "password123"
    },
    {
      "username": "user2",
      "email": "user2@example.com",
      "password": "password123"
    }
  ]'
```

### Bulk Delete
```bash
curl -X DELETE http://localhost:5000/users/bulk \
  -H "Content-Type: application/json" \
  -d '[1, 2, 3]'
```

## Key Concepts Demonstrated

1. **Complete CRUD Operations** - Create, Read, Update, Delete
2. **Pagination** - List endpoints with page/per_page
3. **Filtering** - Filter by active status, search by text
4. **Validation** - Pydantic models with field constraints
5. **Error Handling** - Proper 404 and 400 errors
6. **Bulk Operations** - Create/delete multiple records
7. **Partial Updates** - PATCH for updating specific fields
8. **Data Integrity** - Username and email uniqueness checks

## Next Steps

- [Authentication](authentication.md) - Add user authentication
- [File Uploads](file_uploads.md) - Handle file uploads
- [Testing](../advanced/testing.md) - Write tests for your API
