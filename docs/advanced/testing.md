# Testing

This guide covers testing strategies for FastOpenAPI applications.

## Testing Flask Applications

### Basic Setup

```python
import pytest
from flask import Flask
from pydantic import BaseModel
from fastopenapi import Query, Body
from fastopenapi.routers import FlaskRouter

# Application code
app = Flask(__name__)
router = FlaskRouter(app=app, title="Test API", version="1.0.0")

class Item(BaseModel):
    name: str
    price: float

@router.get("/items/{item_id}")
def get_item(item_id: int):
    return {"id": item_id, "name": "Item"}

@router.post("/items", response_model=Item, status_code=201)
def create_item(item: Item = Body(...)):
    return item

# Test code
@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_get_item(client):
    """Test GET endpoint"""
    response = client.get('/items/1')
    assert response.status_code == 200
    data = response.get_json()
    assert data['id'] == 1
    assert data['name'] == 'Item'

def test_create_item(client):
    """Test POST endpoint"""
    response = client.post('/items', json={
        'name': 'New Item',
        'price': 99.99
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['name'] == 'New Item'
    assert data['price'] == 99.99

def test_validation_error(client):
    """Test validation errors"""
    response = client.post('/items', json={
        'name': 'Item'
        # Missing 'price' field
    })
    assert response.status_code == 422
    data = response.get_json()
    assert 'error' in data
```

---

## Testing Async Frameworks (Starlette)

### Async Test Setup

```python
import pytest
from starlette.applications import Starlette
from starlette.testclient import TestClient
from pydantic import BaseModel
from fastopenapi import Body
from fastopenapi.routers import StarletteRouter

app = Starlette()
router = StarletteRouter(app=app)

class User(BaseModel):
    username: str
    email: str

@router.get("/users/{user_id}")
async def get_user(user_id: int):
    return {"id": user_id, "username": "john"}

@router.post("/users", response_model=User, status_code=201)
async def create_user(user: User = Body(...)):
    return user

# Tests
@pytest.fixture
def client():
    """Create Starlette test client"""
    return TestClient(app)

def test_get_user(client):
    """Test GET endpoint"""
    response = client.get('/users/1')
    assert response.status_code == 200
    assert response.json()['id'] == 1

def test_create_user(client):
    """Test POST endpoint"""
    response = client.post('/users', json={
        'username': 'john',
        'email': 'john@example.com'
    })
    assert response.status_code == 201
    assert response.json()['username'] == 'john'
```

---

## Testing with Dependencies

### Mocking Dependencies

```python
from fastopenapi import Depends

# Real dependency
def get_db():
    db = DatabaseConnection()
    try:
        yield db
    finally:
        db.close()

@router.get("/items")
def list_items(db = Depends(get_db)):
    items = db.query_items()
    return items

# Test code
class MockDB:
    """Mock database"""
    def query_items(self):
        return [{"id": 1, "name": "Test Item"}]

@pytest.fixture
def mock_db():
    """Mock database dependency"""
    return MockDB()

def test_list_items_with_mock(client, mock_db, monkeypatch):
    """Test with mocked dependency"""
    def mock_get_db():
        yield mock_db

    # Replace dependency
    monkeypatch.setattr('your_module.get_db', mock_get_db)

    response = client.get('/items')
    assert response.status_code == 200
    assert len(response.json()) == 1
```

---

## Testing Authentication

### Testing Protected Endpoints

```python
from fastopenapi import Header, Depends
from fastopenapi.errors import AuthenticationError

# Auth dependency
def get_current_user(authorization: str = Header(..., alias="Authorization")):
    if authorization != "Bearer valid_token":
        raise AuthenticationError("Invalid token")
    return {"id": 1, "username": "john"}

@router.get("/protected")
def protected_endpoint(user = Depends(get_current_user)):
    return {"message": f"Hello, {user['username']}!"}

# Tests
def test_protected_endpoint_without_auth(client):
    """Test without authorization"""
    response = client.get('/protected')
    assert response.status_code == 401

def test_protected_endpoint_with_invalid_token(client):
    """Test with invalid token"""
    response = client.get('/protected', headers={
        'Authorization': 'Bearer invalid_token'
    })
    assert response.status_code == 401

def test_protected_endpoint_with_valid_token(client):
    """Test with valid token"""
    response = client.get('/protected', headers={
        'Authorization': 'Bearer valid_token'
    })
    assert response.status_code == 200
    assert 'Hello, john!' in response.json()['message']
```

---

## Testing with Database

### Using Test Database

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Test database setup
@pytest.fixture(scope='function')
def test_db():
    """Create test database"""
    engine = create_engine('sqlite:///:memory:')
    TestSessionLocal = sessionmaker(bind=engine)

    # Create tables
    Base.metadata.create_all(bind=engine)

    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_create_user(client, test_db, monkeypatch):
    """Test user creation with test database"""
    def get_test_db():
        try:
            yield test_db
        finally:
            pass

    monkeypatch.setattr('your_module.get_db', get_test_db)

    response = client.post('/users', json={
        'username': 'testuser',
        'email': 'test@example.com'
    })

    assert response.status_code == 201

    # Verify in database
    user = test_db.query(User).filter_by(username='testuser').first()
    assert user is not None
    assert user.email == 'test@example.com'
```

---

## Testing File Uploads

```python
from io import BytesIO
from fastopenapi import File, FileUpload

@router.post("/upload")
def upload_file(file: FileUpload = File(...)):
    content = file.read()
    return {
        "filename": file.filename,
        "size": len(content)
    }

# Test
def test_file_upload(client):
    """Test file upload"""
    data = {
        'file': (BytesIO(b'test file content'), 'test.txt')
    }

    response = client.post('/upload', files=data)

    assert response.status_code == 200
    assert response.json()['filename'] == 'test.txt'
    assert response.json()['size'] > 0

def test_multiple_file_upload(client):
    """Test multiple file upload"""
    data = {
        'files': [
            (BytesIO(b'file 1'), 'file1.txt'),
            (BytesIO(b'file 2'), 'file2.txt')
        ]
    }

    response = client.post('/upload-multiple', files=data)
    assert response.status_code == 200
```

---

## Testing Query Parameters

```python
@router.get("/items")
def list_items(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str = Query(None)
):
    return {
        "page": page,
        "limit": limit,
        "search": search
    }

# Tests
def test_query_parameters_defaults(client):
    """Test with default query parameters"""
    response = client.get('/items')
    assert response.status_code == 200
    data = response.json()
    assert data['page'] == 1
    assert data['limit'] == 10
    assert data['search'] is None

def test_query_parameters_custom(client):
    """Test with custom query parameters"""
    response = client.get('/items?page=2&limit=20&search=laptop')
    assert response.status_code == 200
    data = response.json()
    assert data['page'] == 2
    assert data['limit'] == 20
    assert data['search'] == 'laptop'

def test_query_parameters_validation(client):
    """Test query parameter validation"""
    response = client.get('/items?page=0')  # page must be >= 1
    assert response.status_code == 422
```

---

## Testing Error Handling

```python
from fastopenapi.errors import ResourceNotFoundError, BadRequestError

@router.get("/items/{item_id}")
def get_item(item_id: int):
    if item_id > 100:
        raise ResourceNotFoundError(f"Item {item_id} not found")
    return {"id": item_id}

@router.post("/items")
def create_item(name: str):
    if not name.strip():
        raise BadRequestError("Name cannot be empty")
    return {"name": name}

# Tests
def test_not_found_error(client):
    """Test 404 error"""
    response = client.get('/items/999')
    assert response.status_code == 404
    data = response.json()
    assert 'error' in data
    assert data['error']['type'] == 'resource_not_found'

def test_bad_request_error(client):
    """Test 400 error"""
    response = client.post('/items', json={'name': '  '})
    assert response.status_code == 400
    data = response.json()
    assert 'error' in data
```

---

## Testing Response Models

```python
from pydantic import BaseModel

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    return {
        "id": user_id,
        "username": "john",
        "email": "john@example.com",
        "password_hash": "secret"  # This will be excluded
    }

# Test
def test_response_model_excludes_fields(client):
    """Test response model excludes extra fields"""
    response = client.get('/users/1')
    assert response.status_code == 200
    data = response.json()

    # Included fields
    assert 'id' in data
    assert 'username' in data
    assert 'email' in data

    # Excluded field
    assert 'password_hash' not in data
```

---

## Fixtures and Test Organization

### Conftest.py

```python
# conftest.py
import pytest
from flask import Flask
from your_app import create_app

@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    app = create_app({
        'TESTING': True,
        'DATABASE_URL': 'sqlite:///:memory:'
    })
    return app

@pytest.fixture(scope='function')
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture(scope='function')
def auth_headers():
    """Authentication headers"""
    return {'Authorization': 'Bearer test_token'}

@pytest.fixture(scope='function')
def sample_user():
    """Sample user data"""
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123'
    }
```

### Test Organization

```
tests/
   conftest.py
   test_users.py
   test_products.py
   test_orders.py
   test_auth.py
```

---

## Coverage

### Running with Coverage

```bash
# Install pytest and coverage
pip install pytest pytest-cov

# Run tests with coverage
pytest --cov=fastopenapi --cov-report=html

# View coverage report
# Opens htmlcov/index.html
```

### Coverage Configuration

```ini
# .coveragerc
[run]
source = your_app
omit =
    */tests/*
    */venv/*
    */migrations/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
```

---

## Integration Tests

```python
import pytest
from your_app import create_app, db

@pytest.fixture(scope='module')
def test_client():
    """Integration test client"""
    app = create_app('testing')

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

def test_user_workflow(test_client):
    """Test complete user workflow"""
    # Register
    response = test_client.post('/auth/register', json={
        'username': 'john',
        'email': 'john@example.com',
        'password': 'password123'
    })
    assert response.status_code == 201

    # Login
    response = test_client.post('/auth/login', json={
        'username': 'john',
        'password': 'password123'
    })
    assert response.status_code == 200
    token = response.json()['access_token']

    # Access protected endpoint
    response = test_client.get('/users/me', headers={
        'Authorization': f'Bearer {token}'
    })
    assert response.status_code == 200
    assert response.json()['username'] == 'john'
```

---

## Best Practices

### 1. Test Each Endpoint

```python
# Test all HTTP methods
def test_get_items(client):
    ...

def test_create_item(client):
    ...

def test_update_item(client):
    ...

def test_delete_item(client):
    ...
```

### 2. Test Validation

```python
def test_valid_input(client):
    """Test with valid input"""
    ...

def test_invalid_input(client):
    """Test with invalid input"""
    ...

def test_missing_required_field(client):
    """Test missing required fields"""
    ...
```

### 3. Test Error Cases

```python
def test_not_found(client):
    """Test 404 error"""
    ...

def test_unauthorized(client):
    """Test 401 error"""
    ...

def test_forbidden(client):
    """Test 403 error"""
    ...
```

### 4. Use Descriptive Test Names

```python
# Good
def test_create_user_with_valid_data_returns_201():
    ...

# Avoid
def test_user():
    ...
```

### 5. Isolate Tests

```python
# Good - each test is independent
def test_create_user(client, test_db):
    # Fresh database for each test
    ...

# Avoid - tests depend on each other
def test_1_create_user():
    ...

def test_2_update_user():
    # Depends on test_1
    ...
```

---

## See Also

- [pytest Documentation](https://docs.pytest.org/) - Pytest testing framework
- [Flask Testing](https://flask.palletsprojects.com/en/latest/testing/) - Flask testing guide
- [Starlette Testing](https://www.starlette.io/testclient/) - Starlette test client
