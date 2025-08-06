from unittest.mock import MagicMock

import pytest

from fastopenapi.core.router import BaseRouter, RouteInfo


class TestBaseRouter:
    def setup_method(self):
        self.app_mock = MagicMock()

        # Create router instance with overridden _register_docs_endpoints method
        class TestRouter(BaseRouter):
            def _register_docs_endpoints(self):
                pass

        self.router = TestRouter(
            app=self.app_mock,
            title="Test API",
            version="1.0.0",
            description="Test API Description",
        )

        self.router_no_app = TestRouter()

    def test_init(self):
        # Test that constructor properly initializes the object
        assert self.router.app == self.app_mock
        assert self.router.title == "Test API"
        assert self.router.version == "1.0.0"
        assert self.router.description == "Test API Description"
        assert self.router.docs_url == "/docs"
        assert self.router.redoc_url == "/redoc"
        assert self.router.openapi_url == "/openapi.json"
        assert self.router.openapi_version == "3.0.0"
        assert self.router._routes == []
        assert self.router._openapi_schema is None

    def test_init_without_app(self):
        assert self.router_no_app.app is None
        assert self.router_no_app.title == "My App"
        assert self.router_no_app.version == "0.1.0"
        assert self.router_no_app.description == "API documentation"
        assert self.router_no_app.docs_url == "/docs"
        assert self.router_no_app.redoc_url == "/redoc"
        assert self.router_no_app.openapi_url == "/openapi.json"
        assert self.router_no_app.openapi_version == "3.0.0"
        assert self.router_no_app._routes == []
        assert self.router_no_app._openapi_schema is None

    def test_add_route(self):
        # Test adding a route to the router
        def test_endpoint():
            pass

        self.router.add_route("/test", "GET", test_endpoint)
        assert len(self.router._routes) == 1
        route = self.router._routes[0]
        assert isinstance(route, RouteInfo)
        assert route.path == "/test"
        assert route.method == "GET"
        assert route.endpoint == test_endpoint

    def test_get_routes(self):
        # Test getting all routes
        def test_endpoint():
            pass

        self.router.add_route("/test1", "GET", test_endpoint)
        self.router.add_route("/test2", "POST", test_endpoint)

        routes = self.router.get_routes()
        assert len(routes) == 2
        assert all(isinstance(r, RouteInfo) for r in routes)
        assert routes[0].path == "/test1"
        assert routes[0].method == "GET"
        assert routes[1].path == "/test2"
        assert routes[1].method == "POST"

    def test_include_router(self):
        # Test including routes from another router
        def test_endpoint():
            pass

        # Create another router
        other_router = BaseRouter()
        other_router.add_route("/other", "GET", test_endpoint)

        # Include the other router with a prefix
        self.router.include_router(other_router, prefix="/api")
        assert len(self.router._routes) == 1
        assert self.router._routes[0].path == "/api/other"

        # Include without prefix
        self.router.include_router(other_router)
        assert len(self.router._routes) == 2
        assert self.router._routes[1].path == "/other"

    def test_http_method_decorators(self):
        # Test all HTTP method decorators

        @self.router.get("/get", tags=["test"])
        def get_endpoint():
            pass

        @self.router.post("/post")
        def post_endpoint():
            pass

        @self.router.put("/put")
        def put_endpoint():
            pass

        @self.router.patch("/patch")
        def patch_endpoint():
            pass

        @self.router.delete("/delete")
        def delete_endpoint():
            pass

        @self.router.head("/head")
        def head_endpoint():
            pass

        @self.router.options("/options")
        def options_endpoint():
            pass

        # Verify routes were added correctly
        routes = self.router.get_routes()
        assert len(routes) == 7

        methods = [route.method for route in routes]
        paths = [route.path for route in routes]

        assert "GET" in methods
        assert "POST" in methods
        assert "PUT" in methods
        assert "PATCH" in methods
        assert "DELETE" in methods
        assert "HEAD" in methods
        assert "OPTIONS" in methods

        assert "/get" in paths
        assert "/post" in paths
        assert "/put" in paths
        assert "/patch" in paths
        assert "/delete" in paths
        assert "/head" in paths
        assert "/options" in paths

        # Check that metadata was properly attached
        assert hasattr(get_endpoint, "__route_meta__")
        assert get_endpoint.__route_meta__["tags"] == ["test"]

    def test_openapi_property_lazy_loading(self):
        # Test the openapi property (lazy loading)

        @self.router.get("/test")
        def test_endpoint():
            pass

        # First call should generate the schema
        schema1 = self.router.openapi
        assert self.router._openapi_schema is not None

        # Second call should return cached schema
        schema2 = self.router.openapi
        assert schema1 is schema2

    def test_register_docs_endpoints_not_implemented(self):
        # Test that base class raises NotImplementedError
        router = BaseRouter()

        with pytest.raises(NotImplementedError):
            router._register_docs_endpoints()
