# Django Integration

Django is one of the most popular Python web frameworks. This guide shows how to use FastOpenAPI with Django, supporting both synchronous (WSGI) and asynchronous (ASGI) modes.

## Installation

```bash
pip install fastopenapi[django]
```

## Basic Setup

FastOpenAPI provides two routers for Django:
- `DjangoRouter` - for synchronous views (WSGI)
- `DjangoAsyncRouter` - for asynchronous views (ASGI)

### Synchronous Django (WSGI)

```python
from django.conf import settings
from django.urls import path, include
from pydantic import BaseModel
from fastopenapi.routers import DjangoRouter

# Configure Django settings (if running standalone)
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='your-secret-key',
        ROOT_URLCONF=__name__,
        ALLOWED_HOSTS=['*'],
    )

router = DjangoRouter(
    app=True,
    title="Django API",
    version="1.0.0"
)

class Item(BaseModel):
    name: str
    price: float

@router.get("/")
def root():
    return {"message": "Hello from Django!"}

@router.post("/items", response_model=Item, status_code=201)
def create_item(item: Item):
    return item

# URL Configuration
urlpatterns = [
    path("", include(router.urls)),
]

if __name__ == "__main__":
    from django.core.management import execute_from_command_line
    execute_from_command_line(["manage.py", "runserver", "8000"])
```

### Asynchronous Django (ASGI)

```python
from django.conf import settings
from django.urls import path, include
from pydantic import BaseModel
from fastopenapi.routers import DjangoAsyncRouter

# Configure Django settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='your-secret-key',
        ROOT_URLCONF=__name__,
        ALLOWED_HOSTS=['*'],
    )

router = DjangoAsyncRouter(
    app=True,
    title="Django Async API",
    version="1.0.0"
)

class Item(BaseModel):
    name: str
    price: float

@router.get("/")
async def root():
    return {"message": "Hello from async Django!"}

@router.post("/items", response_model=Item, status_code=201)
async def create_item(item: Item):
    return item

# URL Configuration
urlpatterns = [
    path("", include(router.urls)),
]

if __name__ == "__main__":
    import uvicorn
    from django.core.asgi import get_asgi_application
    
    application = get_asgi_application()
    uvicorn.run(application, host="127.0.0.1", port=8000)
```

## Integration with Django Project

### In settings.py

```python
# settings.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'your_app',
]

# Optional: Disable CSRF for API endpoints
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',  # Disabled for API
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

### In urls.py

```python
# urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('your_app.api')),
]
```

### In your_app/api.py

```python
# your_app/api.py
from pydantic import BaseModel
from fastopenapi.routers import DjangoRouter

router = DjangoRouter(
    app=True,
    title="Your App API",
    version="1.0.0"
)

class Item(BaseModel):
    name: str
    price: float

@router.get("/items")
def list_items():
    return {"items": []}

@router.post("/items", response_model=Item, status_code=201)
def create_item(item: Item):
    return item

# Export URLs
urls = router.urls
```

## Path Parameters

```python
from fastopenapi import Path

@router.get("/users/{user_id}")
def get_user(user_id: int = Path(..., description="User ID")):
    return {"user_id": user_id}

# Django URL: /users/<user_id>
```

## Request Data

### Query Parameters

```python
from fastopenapi import Query

@router.get("/search")
def search(
    q: str = Query(..., description="Search query"),
    page: int = Query(1, ge=1)
):
    return {"query": q, "page": page}
```

### Request Body

```python
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

@router.post("/users", status_code=201)
def create_user(user: UserCreate):
    # user is automatically validated
    return {"username": user.username, "email": user.email}
```

### Form Data

```python
from fastopenapi import Form

@router.post("/login")
def login(
    username: str = Form(...),
    password: str = Form(...)
):
    # Authenticate user
    return {"username": username}
```

### File Upload

```python
from fastopenapi import File, FileUpload

# Synchronous
@router.post("/upload")
def upload_file(file: FileUpload = File(...)):
    content = file.read()  # Sync read
    return {
        "filename": file.filename,
        "size": len(content),
        "content_type": file.content_type
    }

# Asynchronous
@router.post("/upload")
async def upload_file_async(file: FileUpload = File(...)):
    content = await file.aread()  # Async read
    return {
        "filename": file.filename,
        "size": len(content)
    }
```

## Working with Django ORM

### Synchronous ORM

```python
from django.contrib.auth.models import User
from fastopenapi.errors import ResourceNotFoundError

@router.get("/users/{user_id}")
def get_user(user_id: int):
    try:
        user = User.objects.get(id=user_id)
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    except User.DoesNotExist:
        raise ResourceNotFoundError(f"User {user_id} not found")

@router.get("/users")
def list_users(limit: int = Query(10, le=100)):
    users = User.objects.all()[:limit]
    return [
        {"id": u.id, "username": u.username, "email": u.email}
        for u in users
    ]
```

### Asynchronous ORM

Django 4.1+ supports async ORM queries:

```python
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async

@router.get("/users/{user_id}")
async def get_user(user_id: int):
    try:
        user = await User.objects.aget(id=user_id)
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    except User.DoesNotExist:
        raise ResourceNotFoundError(f"User {user_id} not found")

@router.get("/users")
async def list_users(limit: int = Query(10)):
    users = []
    async for user in User.objects.all()[:limit]:
        users.append({
            "id": user.id,
            "username": user.username,
            "email": user.email
        })
    return users
```

### Using sync_to_async

For synchronous ORM code in async views:

```python
from asgiref.sync import sync_to_async

@sync_to_async
def get_user_from_db(user_id: int):
    return User.objects.get(id=user_id)

@router.get("/users/{user_id}")
async def get_user(user_id: int):
    try:
        user = await get_user_from_db(user_id)
        return {"id": user.id, "username": user.username}
    except User.DoesNotExist:
        raise ResourceNotFoundError(f"User {user_id} not found")
```

## Django-Specific Features

### Using Django Request

```python
from django.http import HttpRequest

@router.get("/request-info")
def get_request_info():
    # Access Django request via thread locals if needed
    # Or use dependencies
    return {"message": "Request info"}
```

### Django Authentication

```python
from django.contrib.auth import authenticate
from fastopenapi.errors import AuthenticationError

@router.post("/auth/login")
def login(username: str = Form(...), password: str = Form(...)):
    user = authenticate(username=username, password=password)
    if user is None:
        raise AuthenticationError("Invalid credentials")
    
    # Create session or token
    return {"user_id": user.id, "username": user.username}
```

### Using Django Models as Response

```python
from django.contrib.auth.models import User
from pydantic import BaseModel

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    
    class Config:
        from_attributes = True  # Allows creating from Django models

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    user = User.objects.get(id=user_id)
    return user  # Pydantic will extract fields from Django model
```

## Error Handling

### Using FastOpenAPI Errors

```python
from fastopenapi.errors import (
    BadRequestError,
    ResourceNotFoundError,
    AuthenticationError
)

@router.get("/items/{item_id}")
def get_item(item_id: int):
    if item_id < 0:
        raise BadRequestError("Item ID must be positive")
    
    # Get from database
    item = database.get(item_id)
    if not item:
        raise ResourceNotFoundError(f"Item {item_id} not found")
    
    return item
```

### Using Django Exceptions

```python
from django.http import Http404
from django.core.exceptions import PermissionDenied

@router.get("/users/{user_id}")
def get_user(user_id: int):
    try:
        user = User.objects.get(id=user_id)
        return {"username": user.username}
    except User.DoesNotExist:
        raise Http404("User not found")

@router.delete("/users/{user_id}")
def delete_user(user_id: int):
    if not has_permission():
        raise PermissionDenied("Not allowed")
    
    User.objects.filter(id=user_id).delete()
    return None
```

## Middleware Integration

Django middleware works normally with FastOpenAPI:

```python
# middleware.py
class CustomMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Before view
        request.custom_data = "example"
        
        response = self.get_response(request)
        
        # After view
        response['X-Custom-Header'] = 'value'
        
        return response

# settings.py
MIDDLEWARE = [
    # ...
    'your_app.middleware.CustomMiddleware',
]
```

## Authentication with Dependencies

```python
from fastopenapi import Depends, Header
from fastopenapi.errors import AuthenticationError

def get_current_user(authorization: str = Header(..., alias="Authorization")):
    """Extract user from Authorization header"""
    if not authorization.startswith("Bearer "):
        raise AuthenticationError("Invalid authorization header")
    
    token = authorization[7:]
    # Validate token and get user
    user = validate_token(token)
    if not user:
        raise AuthenticationError("Invalid token")
    
    return user

@router.get("/profile")
def get_profile(user = Depends(get_current_user)):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email
    }
```

## Database Transactions

### Synchronous

```python
from django.db import transaction

@router.post("/transfer", status_code=200)
def transfer_money(
    from_account: int = Form(...),
    to_account: int = Form(...),
    amount: float = Form(...)
):
    with transaction.atomic():
        # Perform transfer
        account_from = Account.objects.select_for_update().get(id=from_account)
        account_to = Account.objects.select_for_update().get(id=to_account)
        
        account_from.balance -= amount
        account_to.balance += amount
        
        account_from.save()
        account_to.save()
    
    return {"message": "Transfer successful"}
```

### Asynchronous

```python
from asgiref.sync import sync_to_async
from django.db import transaction

@router.post("/transfer", status_code=200)
async def transfer_money(
    from_account: int = Form(...),
    to_account: int = Form(...),
    amount: float = Form(...)
):
    @sync_to_async
    @transaction.atomic
    def do_transfer():
        account_from = Account.objects.select_for_update().get(id=from_account)
        account_to = Account.objects.select_for_update().get(id=to_account)
        
        account_from.balance -= amount
        account_to.balance += amount
        
        account_from.save()
        account_to.save()
    
    await do_transfer()
    return {"message": "Transfer successful"}
```

## CORS Support

Use django-cors-headers:

```bash
pip install django-cors-headers
```

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    # ...
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://example.com",
]

# Or allow all (development only)
CORS_ALLOW_ALL_ORIGINS = True
```

## Complete Example

```python
# settings.py
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-secret-key'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

ROOT_URLCONF = 'project.urls'
```

```python
# api.py
from django.contrib.auth.models import User
from pydantic import BaseModel, EmailStr
from fastopenapi.routers import DjangoRouter
from fastopenapi.errors import ResourceNotFoundError
from fastopenapi import Query

router = DjangoRouter(
    app=True,
    title="User Management API",
    version="1.0.0",
    description="Django API with FastOpenAPI"
)

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

@router.get("/", tags=["Root"])
def root():
    """Root endpoint"""
    return {"message": "User Management API"}

@router.get("/users", response_model=list[UserResponse], tags=["Users"])
def list_users(limit: int = Query(10, ge=1, le=100)):
    """List all users"""
    users = User.objects.all()[:limit]
    return list(users)

@router.get("/users/{user_id}", response_model=UserResponse, tags=["Users"])
def get_user(user_id: int):
    """Get user by ID"""
    try:
        user = User.objects.get(id=user_id)
        return user
    except User.DoesNotExist:
        raise ResourceNotFoundError(f"User {user_id} not found")

@router.post("/users", response_model=UserResponse, status_code=201, tags=["Users"])
def create_user(user: UserCreate):
    """Create new user"""
    new_user = User.objects.create_user(
        username=user.username,
        email=user.email,
        password=user.password
    )
    return new_user

@router.delete("/users/{user_id}", status_code=204, tags=["Users"])
def delete_user(user_id: int):
    """Delete user"""
    try:
        user = User.objects.get(id=user_id)
        user.delete()
        return None
    except User.DoesNotExist:
        raise ResourceNotFoundError(f"User {user_id} not found")

urls = router.urls
```

```python
# urls.py
from django.contrib import admin
from django.urls import path, include
import api

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(api.urls)),
]
```

## Running the Server

### Development (Synchronous)

```bash
python manage.py runserver 8000
```

### Development (Asynchronous)

```bash
# Install uvicorn
pip install uvicorn

# Run with uvicorn
uvicorn project.asgi:application --host 0.0.0.0 --port 8000 --reload
```

### Production

```bash
# With Gunicorn (sync)
gunicorn project.wsgi:application --bind 0.0.0.0:8000 --workers 4

# With Uvicorn (async)
uvicorn project.asgi:application --host 0.0.0.0 --port 8000 --workers 4
```

## Testing

```python
from django.test import TestCase, Client

class APITestCase(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_root(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'User Management API')
    
    def test_create_user(self):
        response = self.client.post('/users', {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['username'], 'testuser')
    
    def test_get_user_not_found(self):
        response = self.client.get('/users/9999')
        self.assertEqual(response.status_code, 404)
```

## Tips and Best Practices

### 1. Choose Right Router

```python
# Use DjangoRouter for sync views
from fastopenapi.routers import DjangoRouter

# Use DjangoAsyncRouter for async views
from fastopenapi.routers import DjangoAsyncRouter
```

### 2. Use Django's Built-in Features

```python
# Use Django's authentication
from django.contrib.auth import authenticate, login

# Use Django's caching
from django.core.cache import cache

# Use Django's signals
from django.db.models.signals import post_save
```

### 3. Leverage Pydantic with Django Models

```python
class UserResponse(BaseModel):
    id: int
    username: str
    
    class Config:
        from_attributes = True  # Important for Django models

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    user = User.objects.get(id=user_id)
    return user  # Pydantic will convert automatically
```

### 4. Handle Django Exceptions

FastOpenAPI automatically converts common Django exceptions:

```python
# These are automatically handled:
# - Http404 -> 404 error
# - PermissionDenied -> 403 error
# - BadRequest -> 400 error
```

## Next Steps

- [Core Concepts](../getting_started/core_concepts.md) - Understand FastOpenAPI
- [Routing](../guide/routing.md) - Learn about routing
- [Dependencies](../guide/dependencies.md) - Use dependency injection
- [Examples](../examples/crud_api.md) - See complete examples
