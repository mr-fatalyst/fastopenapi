# CRUD API Example

This example demonstrates building a complete CRUD (Create, Read, Update, Delete) API for managing users using FastOpenAPI.

## Complete Example

```python
import hashlib
from datetime import datetime

from flask import Flask
from pydantic import BaseModel, EmailStr, Field

from fastopenapi import Query
from fastopenapi.errors import BadRequestError, ResourceNotFoundError
from fastopenapi.routers import FlaskRouter

app = Flask(__name__)
router = FlaskRouter(
    app=app,
    title="User Management API",
    version="1.0.0",
    description="Complete CRUD API for user management",
)

# In-memory database
users_db: dict[int, dict] = {}
next_id = 1


# Models
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str | None = Field(None, max_length=100)
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    username: str | None = Field(None, min_length=3, max_length=50)
    email: EmailStr | None = None
    full_name: str | None = Field(None, max_length=100)
    password: str | None = Field(None, min_length=8)
    is_active: bool | None = None


class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class BulkUserCreate(BaseModel):
    users: list[UserCreate]


class BulkUserDelete(BaseModel):
    user_ids: list[int]


class BulkResultResponse(BaseModel):
    success_count: int
    success_ids: list[int]
    error_count: int
    errors: list[dict]


# Helpers
def hash_password(password: str) -> str:
    """Simplified hash — use bcrypt in production."""
    return hashlib.sha256(password.encode()).hexdigest()


def find_user(username: str | None = None, email: str | None = None) -> dict | None:
    for user in users_db.values():
        if username and user["username"] == username:
            return user
        if email and user["email"] == email:
            return user
    return None


def user_response(user: dict) -> dict:
    """Strip internal fields before returning."""
    return {k: v for k, v in user.items() if k != "password_hash"}


def check_unique(username: str, email: str, exclude_id: int | None = None):
    existing = find_user(username=username)
    if existing and existing["id"] != exclude_id:
        raise BadRequestError(f"Username '{username}' already exists")
    existing = find_user(email=email)
    if existing and existing["id"] != exclude_id:
        raise BadRequestError(f"Email '{email}' already exists")


# Endpoints

@router.get("/", tags=["Root"])
def root():
    return {
        "message": "User Management API",
        "version": "1.0.0",
    }


@router.get("/users", response_model=UserListResponse, tags=["Users"])
def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Users per page"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    search: str | None = Query(None, description="Search in username or email"),
):
    users = list(users_db.values())

    if is_active is not None:
        users = [u for u in users if u["is_active"] == is_active]
    if search:
        q = search.lower()
        users = [u for u in users if q in u["username"].lower() or q in u["email"].lower()]

    total = len(users)
    total_pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    page_users = users[start : start + per_page]

    return {
        "users": [user_response(u) for u in page_users],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


@router.get("/users/{user_id}", response_model=UserResponse, tags=["Users"])
def get_user(user_id: int):
    user = users_db.get(user_id)
    if not user:
        raise ResourceNotFoundError(f"User with ID {user_id} not found")
    return user_response(user)


@router.post("/users", response_model=UserResponse, status_code=201, tags=["Users"])
def create_user(user: UserCreate):
    global next_id

    check_unique(user.username, user.email)

    now = datetime.now()
    new_user = {
        "id": next_id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "password_hash": hash_password(user.password),
        "created_at": now,
        "updated_at": now,
    }
    users_db[next_id] = new_user
    next_id += 1

    return user_response(new_user)


@router.put("/users/{user_id}", response_model=UserResponse, tags=["Users"])
def replace_user(user_id: int, user: UserCreate):
    existing = users_db.get(user_id)
    if not existing:
        raise ResourceNotFoundError(f"User with ID {user_id} not found")

    check_unique(user.username, user.email, exclude_id=user_id)

    updated = {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "password_hash": hash_password(user.password),
        "created_at": existing["created_at"],
        "updated_at": datetime.now(),
    }
    users_db[user_id] = updated

    return user_response(updated)


@router.patch("/users/{user_id}", response_model=UserResponse, tags=["Users"])
def update_user(user_id: int, updates: UserUpdate):
    user = users_db.get(user_id)
    if not user:
        raise ResourceNotFoundError(f"User with ID {user_id} not found")

    data = updates.model_dump(exclude_unset=True)

    if "username" in data:
        existing = find_user(username=data["username"])
        if existing and existing["id"] != user_id:
            raise BadRequestError(f"Username '{data['username']}' already exists")

    if "email" in data:
        existing = find_user(email=data["email"])
        if existing and existing["id"] != user_id:
            raise BadRequestError(f"Email '{data['email']}' already exists")

    if "password" in data:
        data["password_hash"] = hash_password(data.pop("password"))

    user.update(data)
    user["updated_at"] = datetime.now()

    return user_response(user)


@router.delete("/users/{user_id}", status_code=204, tags=["Users"])
def delete_user(user_id: int):
    if user_id not in users_db:
        raise ResourceNotFoundError(f"User with ID {user_id} not found")
    del users_db[user_id]
    return None


# Bulk operations

@router.post("/users/bulk", response_model=BulkResultResponse, status_code=201, tags=["Bulk Operations"])
def bulk_create_users(payload: BulkUserCreate):
    global next_id
    created = []
    errors = []

    for idx, user in enumerate(payload.users):
        if find_user(username=user.username):
            errors.append({"index": idx, "error": f"Username '{user.username}' already exists"})
            continue
        if find_user(email=user.email):
            errors.append({"index": idx, "error": f"Email '{user.email}' already exists"})
            continue

        now = datetime.now()
        users_db[next_id] = {
            "id": next_id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "password_hash": hash_password(user.password),
            "created_at": now,
            "updated_at": now,
        }
        created.append(next_id)
        next_id += 1

    return {"success_count": len(created), "success_ids": created, "error_count": len(errors), "errors": errors}


@router.post("/users/bulk-delete", response_model=BulkResultResponse, tags=["Bulk Operations"])
def bulk_delete_users(payload: BulkUserDelete):
    deleted = []
    errors = []

    for uid in payload.user_ids:
        if uid in users_db:
            del users_db[uid]
            deleted.append(uid)
        else:
            errors.append({"user_id": uid, "error": "User not found"})

    return {"success_count": len(deleted), "success_ids": deleted, "error_count": len(errors), "errors": errors}


if __name__ == "__main__":
    for name, email in [("alice", "alice@example.com"), ("bob", "bob@example.com")]:
        create_user(UserCreate(username=name, email=email, full_name=name.title(), password="password123"))

    print("Sample users created! Docs at http://localhost:5000/docs")
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
  -d '{
    "users": [
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
    ]
  }'
```

### Bulk Delete
```bash
curl -X POST http://localhost:5000/users/bulk-delete \
  -H "Content-Type: application/json" \
  -d '{"user_ids": [1, 2, 3]}'
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
