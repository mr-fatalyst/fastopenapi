from collections.abc import Callable
from typing import Any


class RouteInfo:
    """Container for route information"""

    def __init__(self, path: str, method: str, endpoint: Callable, meta: dict):
        self.path = path
        self.method = method.upper()
        self.endpoint = endpoint
        self.meta = meta


class BaseRouter:
    """
    Base router that collects routes and generates an OpenAPI schema.
    This class is extended by specific framework routers.
    """

    def __init__(
        self,
        app: Any = None,
        docs_url: str | None = "/docs",
        redoc_url: str | None = "/redoc",
        openapi_url: str | None = "/openapi.json",
        openapi_version: str = "3.0.0",
        title: str = "My App",
        version: str = "0.1.0",
        description: str = "API documentation",
    ):
        self.app = app
        self.docs_url = docs_url
        self.redoc_url = redoc_url
        self.openapi_url = openapi_url
        self.openapi_version = openapi_version
        self.title = title
        self.version = version
        self.description = description
        self._routes: list[RouteInfo] = []
        self._openapi_schema = None

        # Register documentation endpoints if app is provided
        if self.app is not None and all([docs_url, redoc_url, openapi_url]):
            self._register_docs_endpoints()

    def add_route(self, path: str, method: str, endpoint: Callable):
        """Add a route to the router"""
        meta = getattr(endpoint, "__route_meta__", {})
        route = RouteInfo(path, method, endpoint, meta)
        self._routes.append(route)

    def include_router(self, other: "BaseRouter", prefix: str = ""):
        """Include routes from another router"""
        for route in other._routes:
            path = (
                f"{prefix.rstrip('/')}/{route.path.lstrip('/')}"
                if prefix
                else route.path
            )
            self.add_route(path, route.method, route.endpoint)

    def get_routes(self) -> list[RouteInfo]:
        """Get all registered routes"""
        return self._routes

    # HTTP method decorators
    def get(self, path: str, **meta):
        return self._create_route_decorator(path, "GET", meta)

    def post(self, path: str, **meta):
        return self._create_route_decorator(path, "POST", meta)

    def put(self, path: str, **meta):
        return self._create_route_decorator(path, "PUT", meta)

    def patch(self, path: str, **meta):
        return self._create_route_decorator(path, "PATCH", meta)

    def delete(self, path: str, **meta):
        return self._create_route_decorator(path, "DELETE", meta)

    def head(self, path: str, **meta):
        return self._create_route_decorator(path, "HEAD", meta)

    def options(self, path: str, **meta):
        return self._create_route_decorator(path, "OPTIONS", meta)

    def _create_route_decorator(self, path: str, method: str, meta: dict):
        """Create a decorator for route registration"""

        def decorator(func: Callable):
            func.__route_meta__ = meta
            self.add_route(path, method, func)
            return func

        return decorator

    def _register_docs_endpoints(self):
        """Register documentation endpoints (to be implemented in routers)"""
        raise NotImplementedError

    @property
    def openapi(self) -> dict:
        """Get OpenAPI schema (lazy loading)"""
        if self._openapi_schema is None:
            from fastopenapi.openapi.generator import OpenAPIGenerator

            generator = OpenAPIGenerator(self)
            self._openapi_schema = generator.generate()
        return self._openapi_schema
