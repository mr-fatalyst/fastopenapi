# Architecture

FastOpenAPI uses modular architecture:

- **BaseRouter**: Abstract base class providing routing and schema generation.
- **Framework Routers**: Specific routers inheriting BaseRouter.

## File Structure

```
fastopenapi/
├── base_router.py
└── routers/
    ├── falcon.py
    ├── flask.py
    ├── quart.py
    ├── sanic.py
    └── starlette.py
```
---
[<< Back](index.md)