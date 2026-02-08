# Flask Integration

Flask is the most popular Python web framework. This guide shows how to use FastOpenAPI with Flask.

## Installation

```bash
pip install fastopenapi[flask]
```

## Basic Setup

```python
from flask import Flask
from pydantic import BaseModel
from fastopenapi.routers import FlaskRouter

app = Flask(__name__)
router = FlaskRouter(
    app=app,
    title="Flask API",
    version="1.0.0"
)

class Item(BaseModel):
    name: str
    price: float

@router.get("/")
def root():
    return {"message": "Hello from Flask!"}

@router.post("/items", response_model=Item, status_code=201)
def create_item(item: Item):
    return item

if __name__ == "__main__":
    app.run(debug=True, port=8000)
```

## Path Parameters

Flask uses `<type:name>` syntax, but FastOpenAPI converts `{name}` automatically:

```python
# FastOpenAPI syntax (preferred)
@router.get("/users/{user_id}")
def get_user(user_id: int):
    return {"user_id": user_id}

# Both generate the same Flask route: /users/<user_id>
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
from pydantic import BaseModel

class User(BaseModel):
    name: str
    email: str
    age: int | None = None

@router.post("/users")
def create_user(user: User):
    # user is automatically validated
    return {"user": user}
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

@router.post("/upload")
def upload_file(file: FileUpload = File(...)):
    content = file.read()  # Synchronous read for Flask
    return {
        "filename": file.filename,
        "size": len(content),
        "content_type": file.content_type
    }
```

## Flask-Specific Features

### Accessing Flask Request

```python
from flask import request

@router.get("/request-info")
def get_request_info():
    return {
        "method": request.method,
        "path": request.path,
        "remote_addr": request.remote_addr,
        "user_agent": request.user_agent.string
    }
```

### Using Flask Response

```python
from flask import make_response, jsonify

@router.get("/custom-response")
def custom_response():
    response = make_response(jsonify({"message": "success"}))
    response.headers["X-Custom-Header"] = "value"
    return response
```

### Flask Sessions

```python
from flask import session

app.secret_key = "your-secret-key"

@router.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    if authenticate(username, password):
        session["user_id"] = get_user_id(username)
        return {"message": "Logged in"}
    raise AuthenticationError("Invalid credentials")

@router.get("/profile")
def profile():
    user_id = session.get("user_id")
    if not user_id:
        raise AuthenticationError("Not logged in")
    return {"user_id": user_id}
```

### Flask Blueprints

You can use FastOpenAPI with Flask blueprints:

```python
from flask import Blueprint

# Create blueprint
api_bp = Blueprint("api", __name__, url_prefix="/api")

# Create router for blueprint
api_router = FlaskRouter(app=api_bp)

@api_router.get("/items")
def list_items():
    return {"items": []}

# Register blueprint
app.register_blueprint(api_bp)
```

## Error Handling

### Using Flask's abort

```python
from flask import abort

@router.get("/users/{user_id}")
def get_user(user_id: int):
    user = database.get(user_id)
    if not user:
        abort(404, description="User not found")
    return user
```

### Using FastOpenAPI Errors

```python
from fastopenapi.errors import ResourceNotFoundError

@router.get("/items/{item_id}")
def get_item(item_id: int):
    item = database.get(item_id)
    if not item:
        raise ResourceNotFoundError(f"Item {item_id} not found")
    return item
```

## Database Integration

### SQLAlchemy

```python
from flask_sqlalchemy import SQLAlchemy
from fastopenapi import Depends

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

def get_db():
    return db.session

@router.get("/users/{user_id}")
def get_user(user_id: int, session = Depends(get_db)):
    user = session.query(User).get(user_id)
    if not user:
        raise ResourceNotFoundError("User not found")
    return {"id": user.id, "name": user.name}
```

## Authentication

### JWT Authentication

```python
import jwt
from datetime import datetime, timedelta
from fastopenapi import Depends, Security, Header

SECRET_KEY = "your-secret-key"

def create_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def get_bearer_token(authorization: str = Header(..., alias="Authorization")):
    if not authorization.startswith("Bearer "):
        raise AuthenticationError("Invalid authorization header")
    return authorization[7:]

def get_current_user(token: str = Depends(get_bearer_token)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["user_id"]
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token")

@router.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    user = authenticate_user(username, password)
    if not user:
        raise AuthenticationError("Invalid credentials")

    token = create_token(user.id)
    return {"access_token": token, "token_type": "bearer"}

@router.get("/protected")
def protected(user_id: int = Security(get_current_user)):
    return {"user_id": user_id}
```

## CORS

Use Flask-CORS for CORS support:

```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Or configure specific origins
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://example.com"],
        "methods": ["GET", "POST"]
    }
})
```

## Deployment

### Development Server

```python
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
```

### Production with Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Production with uWSGI

```bash
pip install uwsgi
uwsgi --http :8000 --wsgi-file app.py --callable app --processes 4
```

## Complete Example

```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from pydantic import BaseModel, EmailStr
from fastopenapi.routers import FlaskRouter
from fastopenapi.errors import ResourceNotFoundError

# Initialize Flask
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
db = SQLAlchemy(app)

# Initialize FastOpenAPI
router = FlaskRouter(
    app=app,
    title="User Management API",
    version="1.0.0",
    description="Flask API with FastOpenAPI"
)

# Database Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)

# Pydantic Models
class UserCreate(BaseModel):
    name: str
    email: EmailStr

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

# Routes
@router.get("/")
def root():
    return {"message": "User Management API"}

@router.get("/users", response_model=list[UserResponse])
def list_users():
    users = User.query.all()
    return [{"id": u.id, "name": u.name, "email": u.email} for u in users]

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    user = User.query.get(user_id)
    if not user:
        raise ResourceNotFoundError(f"User {user_id} not found")
    return {"id": user.id, "name": user.name, "email": user.email}

@router.post("/users", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate):
    new_user = User(name=user.name, email=user.email)
    db.session.add(new_user)
    db.session.commit()
    return {"id": new_user.id, "name": new_user.name, "email": new_user.email}

@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int):
    user = User.query.get(user_id)
    if not user:
        raise ResourceNotFoundError(f"User {user_id} not found")
    db.session.delete(user)
    db.session.commit()
    return None

# Create tables
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True, port=8000)
```

## Testing

```python
import pytest
from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json["message"] == "User Management API"

def test_create_user(client):
    response = client.post("/users", json={
        "name": "John Doe",
        "email": "john@example.com"
    })
    assert response.status_code == 201
    assert response.json["name"] == "John Doe"
```

## Next Steps

- [Core Concepts](../getting_started/core_concepts.md) - Understand FastOpenAPI
- [User Guide](../guide/routing.md) - Learn all features
- [Examples](../examples/crud_api.md) - See complete examples
