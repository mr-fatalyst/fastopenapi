# Installation

FastOpenAPI is available on PyPI and supports Python 3.10 and above.

## Requirements

- **Python 3.10+** - Required for modern type hints and Pydantic v2 support
- **Pydantic v2** - Automatically installed as a dependency
- (Optional) A web framework - Install separately or use extras

## Basic Installation

Install FastOpenAPI using pip:

```bash
pip install fastopenapi
```

This installs the core library with Pydantic v2. You'll need to install your web framework separately if you don't have it already.

## Installation with Framework Extras

To install FastOpenAPI along with a specific framework, use one of the following extras:

### AIOHTTP

```bash
pip install fastopenapi[aiohttp]
```

Installs FastOpenAPI with aiohttp.

### Django

```bash
pip install fastopenapi[django]
```

Installs FastOpenAPI with Django.

### Falcon

```bash
pip install fastopenapi[falcon]
```

Installs FastOpenAPI with Falcon (ASGI/WSGI support).

### Flask

```bash
pip install fastopenapi[flask]
```

Installs FastOpenAPI with Flask.

### Quart

```bash
pip install fastopenapi[quart]
```

Installs FastOpenAPI with Quart (async Flask alternative).

### Sanic

```bash
pip install fastopenapi[sanic]
```

Installs FastOpenAPI with Sanic.

### Starlette

```bash
pip install fastopenapi[starlette]
```

Installs FastOpenAPI with Starlette.

### Tornado

```bash
pip install fastopenapi[tornado]
```

Installs FastOpenAPI with Tornado.

## Installing Multiple Frameworks

If you need to work with multiple frameworks (e.g., for testing or library development), you can install multiple extras:

```bash
pip install fastopenapi[flask,starlette,django]
```

## Development Installation

To contribute to FastOpenAPI or run tests, clone the repository and install in development mode:

```bash
git clone https://github.com/mr-fatalyst/fastopenapi.git
cd fastopenapi
pip install -e ".[dev]"
```

This installs FastOpenAPI in editable mode with all development dependencies including:

- pytest - Testing framework
- black - Code formatter
- flake8 - Linter
- mypy - Type checker
- All supported frameworks for testing

## Verifying Installation

After installation, verify that FastOpenAPI is correctly installed:

```python
import fastopenapi
print(fastopenapi.__version__)
```

You should see the version number (e.g., `1.0.0b1`).

## Upgrading

To upgrade FastOpenAPI to the latest version:

```bash
pip install --upgrade fastopenapi
```

To upgrade with extras:

```bash
pip install --upgrade fastopenapi[flask]
```

## Troubleshooting

### ImportError for a specific framework

If you get an `ImportError` when trying to use a specific router:

```python
from fastopenapi.routers import FlaskRouter
# ImportError: This framework is not installed.
```

**Solution**: Install the framework extra:

```bash
pip install fastopenapi[flask]
```

Or install the framework separately:

```bash
pip install flask
```

### Pydantic v1 vs v2

FastOpenAPI requires **Pydantic v2**. If you have Pydantic v1 installed, you may encounter compatibility issues.

**Check your Pydantic version**:

```bash
pip show pydantic
```

**Upgrade to Pydantic v2**:

```bash
pip install --upgrade "pydantic>=2.0"
```

### Python Version Issues

FastOpenAPI requires Python 3.10 or higher. Check your Python version:

```bash
python --version
```

If you have an older version, consider using [pyenv](https://github.com/pyenv/pyenv) to manage multiple Python versions.

## Next Steps

Now that FastOpenAPI is installed, continue to:

- [Quickstart](quickstart.md) - Build your first API
- [Core Concepts](core_concepts.md) - Understand the fundamentals
- [Framework Guides](../frameworks/overview.md) - Choose your framework
