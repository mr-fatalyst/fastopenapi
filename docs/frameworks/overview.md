# Framework Overview

FastOpenAPI supports 8 popular Python web frameworks. This guide helps you choose the right one for your project.

## Supported Frameworks

| Framework | Type | Async | Python 3.10+ | Best For |
|-----------|------|-------|--------------|----------|
| **Flask** | WSGI | No | Yes | Traditional web apps, simple APIs |
| **Django** | WSGI/ASGI | Both | Yes | Full-featured web applications |
| **Starlette** | ASGI | Yes | Yes | Modern async APIs, high performance |
| **Quart** | ASGI | Yes | Yes | Async Flask alternative |
| **AIOHTTP** | ASGI | Yes | Yes | Async HTTP client/server |
| **Sanic** | ASGI | Yes | Yes | Speed-focused async framework |
| **Falcon** | WSGI/ASGI | Both | Yes | Minimalist APIs, microservices |
| **Tornado** | Async | Yes | Yes | Long-lived connections, WebSockets |

## Quick Comparison

### Flask

**Pros:**
- Most popular Python web framework
- Large ecosystem and community
- Easy to learn
- Extensive documentation
- Many extensions available

**Cons:**
- Synchronous (blocks on I/O)
- Not ideal for high-concurrency scenarios
- Less performant than async alternatives

**Use When:**
- You need maximum compatibility
- Working with synchronous libraries
- Building traditional web applications
- Team is familiar with Flask

**Installation:**
```bash
pip install fastopenapi[flask]
```

### Django

**Pros:**
- Full-featured web framework
- Built-in admin panel, ORM, authentication
- Large community and ecosystem
- Both sync and async support
- Battle-tested in production

**Cons:**
- Heavyweight for simple APIs
- Opinionated structure
- Steeper learning curve

**Use When:**
- Building complex web applications
- Need admin interface
- Want built-in ORM and auth
- Building content-heavy sites

**Installation:**
```bash
pip install fastopenapi[django]
```

### Starlette

**Pros:**
- Modern ASGI framework
- High performance
- Full async support
- WebSocket support
- FastAPI is built on Starlette

**Cons:**
- Smaller ecosystem than Flask/Django
- Requires understanding of async/await
- Less middleware/extensions available

**Use When:**
- Building modern async APIs
- Need high performance
- Want lightweight framework
- Comfortable with async Python

**Installation:**
```bash
pip install fastopenapi[starlette]
```

### Quart

**Pros:**
- Async version of Flask
- Flask-compatible API
- Easy migration from Flask
- WebSocket support

**Cons:**
- Smaller ecosystem than Flask
- Less mature than Flask
- Some Flask extensions don't work

**Use When:**
- Migrating Flask app to async
- Want Flask-like API with async
- Need WebSocket support

**Installation:**
```bash
pip install fastopenapi[quart]
```

### AIOHTTP

**Pros:**
- Mature async framework
- Both client and server
- WebSocket support
- Good for async networking

**Cons:**
- More verbose than others
- Less intuitive routing
- Smaller community

**Use When:**
- Need both HTTP client and server
- Building async networking services
- Working heavily with aiohttp ecosystem

**Installation:**
```bash
pip install fastopenapi[aiohttp]
```

### Sanic

**Pros:**
- Very fast (Flask-like API)
- Built for speed
- Good documentation
- Active development

**Cons:**
- Not compatible with WSGI
- Smaller ecosystem
- Breaking changes between versions

**Use When:**
- Performance is critical
- Want Flask-like async framework
- Building high-throughput APIs

**Installation:**
```bash
pip install fastopenapi[sanic]
```

### Falcon

**Pros:**
- Extremely lightweight
- Very fast
- Minimalist design
- Both WSGI and ASGI

**Cons:**
- Bare-bones (no built-in features)
- Smaller community
- Must add everything yourself

**Use When:**
- Building microservices
- Need minimal overhead
- Want maximum control
- Performance is critical

**Installation:**
```bash
pip install fastopenapi[falcon]
```

### Tornado

**Pros:**
- Mature async framework
- Excellent for WebSockets
- Good for long-polling
- Built-in WebSocket support

**Cons:**
- Older async model (pre async/await)
- Less modern than Starlette/FastAPI
- Smaller community now

**Use When:**
- Need WebSocket support
- Building real-time applications
- Legacy Tornado projects

**Installation:**
```bash
pip install fastopenapi[tornado]
```

## Performance Comparison

Approximate requests/second (higher is better):

```
Starlette:  ~20,000 req/s
Sanic:      ~18,000 req/s
Falcon:     ~15,000 req/s (ASGI)
AIOHTTP:    ~14,000 req/s
Quart:      ~12,000 req/s
Tornado:    ~10,000 req/s
Falcon:     ~8,000 req/s (WSGI)
Flask:      ~5,000 req/s
Django:     ~3,000 req/s
```

Note: These are approximate and depend heavily on your specific use case.

## Sync vs Async

### When to Use Sync (Flask, Django WSGI, Falcon WSGI)

- Working with synchronous libraries (psycopg2, etc.)
- Team unfamiliar with async/await
- Simple CRUD operations
- Traditional web applications
- Lower concurrency requirements

### When to Use Async (Starlette, AIOHTTP, Sanic, Quart, Tornado, Django ASGI, Falcon ASGI)

- High-concurrency requirements
- I/O-bound operations
- WebSocket support needed
- Working with async libraries
- Modern API development

## Migration Guide

### From Flask to Quart

Quart is designed to be Flask-compatible:

```python
# Flask
from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello():
    return {"message": "Hello"}

# Quart (minimal changes)
from quart import Quart
app = Quart(__name__)

@app.route("/")
async def hello():  # Just add async
    return {"message": "Hello"}
```

### From Flask to Starlette

```python
# Flask
from flask import Flask, jsonify
app = Flask(__name__)

@app.route("/items/<int:item_id>")
def get_item(item_id):
    return jsonify({"item_id": item_id})

# Starlette
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

async def get_item(request):
    item_id = request.path_params["item_id"]
    return JSONResponse({"item_id": item_id})

app = Starlette(routes=[
    Route("/items/{item_id:int}", get_item)
])
```

### From Django Views to FastOpenAPI

```python
# Traditional Django view
from django.http import JsonResponse

def get_user(request, user_id):
    user = User.objects.get(id=user_id)
    return JsonResponse({
        "id": user.id,
        "name": user.name
    })

# FastOpenAPI with Django
from fastopenapi.routers import DjangoRouter

router = DjangoRouter(app=True)

@router.get("/users/{user_id}")
def get_user(user_id: int):
    user = User.objects.get(id=user_id)
    return {"id": user.id, "name": user.name}
```

## Feature Matrix

| Feature | Flask | Django | Starlette | Quart | AIOHTTP | Sanic | Falcon | Tornado |
|---------|-------|--------|-----------|-------|---------|-------|--------|---------|
| **Async** | No | Yes* | Yes | Yes | Yes | Yes | Yes* | Yes |
| **WebSockets** | Extension | Yes | Yes | Yes | Yes | Yes | No | Yes |
| **Built-in ORM** | No | Yes | No | No | No | No | No | No |
| **Admin Panel** | No | Yes | No | No | No | No | No | No |
| **File Upload** | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| **Form Handling** | Extension | Yes | Yes | Yes | No | Yes | No | Yes |
| **Session Management** | Extension | Yes | Middleware | Extension | No | Extension | No | Yes |
| **Template Engine** | Jinja2 | Django Templates | Jinja2 | Jinja2 | Jinja2 | Jinja2 | No | Native |
| **Deployment** | WSGI | WSGI/ASGI | ASGI | ASGI | ASGI | ASGI | WSGI/ASGI | ASGI |

*Django and Falcon support both sync and async

## Choosing Your Framework

### For Beginners

**Start with Flask:**
- Easiest to learn
- Best documentation
- Largest community

### For Production APIs

**Choose Starlette or FastAPI:**
- Modern async support
- High performance
- Growing ecosystem

### For Full Web Applications

**Choose Django:**
- Complete solution
- Built-in admin
- Authentication, ORM included

### For Maximum Performance

**Choose Sanic or Starlette:**
- Highest throughput
- Async from ground up
- Optimized for speed

### For Microservices

**Choose Falcon:**
- Minimal overhead
- Very lightweight
- Fast

## Framework-Specific Examples

See detailed guides for each framework:

- [Flask](flask.md) - Synchronous, traditional
- [Django](django.md) - Full-featured framework
- [Starlette](starlette.md) - Modern async
- [Quart](quart.md) - Async Flask
- [AIOHTTP](aiohttp.md) - Async client/server
- [Sanic](sanic.md) - Fast async
- [Falcon](falcon.md) - Minimalist
- [Tornado](tornado.md) - Async networking

## Next Steps

1. Choose a framework based on your needs
2. Follow the framework-specific guide
3. Check out [examples](../examples/crud_api.md) for complete applications
4. Read [core concepts](../getting_started/core_concepts.md) if you haven't
