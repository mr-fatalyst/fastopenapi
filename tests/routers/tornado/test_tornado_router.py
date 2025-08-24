import re

import pytest
import tornado.web

from fastopenapi.routers import TornadoRouter


# Simple endpoint for testing
def dummy_endpoint(**kwargs):
    return "ok"


# Fixture for Tornado application
@pytest.fixture
def dummy_app():
    return tornado.web.Application()


class TestTornadoRouter:
    """Test suite for TornadoRouter class."""

    @pytest.fixture
    def router(self, dummy_app):
        """Router fixture without automatic documentation endpoints registration."""
        return TornadoRouter(
            app=dummy_app,
            title="Test API",
            version="1.0.0",
            description="Dummy description",
            docs_url=None,
            redoc_url=None,
        )

    @pytest.fixture
    def router_with_docs(self):
        """Router fixture with automatic documentation endpoints registration."""
        app = tornado.web.Application()
        return TornadoRouter(
            app=app,
            title="Test API",
            version="1.0.0",
            description="Dummy description",
        )

    @pytest.fixture
    def router_without_app(self):
        """Router fixture without app - for testing app=None case."""
        return TornadoRouter(
            app=None,
            title="Test API",
            version="1.0.0",
            description="Dummy description",
        )

    def test_init_with_app_and_docs(self, router_with_docs):
        """Test initialization when app is provided and docs routes are enabled."""
        # Check that docs routes are registered
        assert len(router_with_docs.routes) >= 3
        route_names = {r.name for r in router_with_docs.routes}
        assert "openapi-schema" in route_names
        assert "swagger-ui" in route_names
        assert "redoc-ui" in route_names

    def test_init_without_app(self, router_without_app):
        """Test initialization when app is None but docs routes are enabled."""
        # When app is None, _register_docs_endpoints doesn't add handlers to app
        # but it should still add routes to the routes list
        assert router_without_app.app is None
        # Routes should be empty since _register_docs_endpoints
        # checks for app is not None
        assert len(router_without_app.routes) == 0

        # Manually call _register_docs_endpoints to test that functionality
        router_without_app._register_docs_endpoints()
        assert len(router_without_app.routes) == 3

    def test_add_route_new(self, router):
        """
        Test adding a new route:
        - The converted path pattern should appear in _endpoint_map with GET method
        - A new URL handler should be added to routes
        - The handler's regex should match the expected pattern (with $ at the end)
        """
        path = "/test/{id}"
        initial_routes = len(router.routes)
        router.add_route(path, "GET", dummy_endpoint)
        expected_pattern = re.sub(r"{(\w+)}", r"(?P<\1>[^/]+)", path)
        expected_full_pattern = expected_pattern + "$"

        # Check _endpoint_map has the new path with GET method
        assert expected_pattern in router._endpoint_map
        assert router._endpoint_map[expected_pattern]["GET"] == dummy_endpoint
        # Check routes count increased by 1
        assert len(router.routes) == initial_routes + 1
        # Check the regex pattern matches expected
        actual_pattern = router.routes[-1].matcher.regex.pattern
        assert actual_pattern == expected_full_pattern

    def test_add_route_duplicate(self, router):
        """
        Test adding a route for a path that already exists:
        - Should not add a new URL handler
        - Should update the endpoint map for that path
        - The regex pattern should remain unchanged (with $ at the end)
        """
        path = "/test/{id}"
        router.add_route(path, "GET", dummy_endpoint)
        initial_routes = len(router.routes)
        expected_pattern = re.sub(r"{(\w+)}", r"(?P<\1>[^/]+)", path)
        assert router._endpoint_map[expected_pattern]["GET"] == dummy_endpoint

        # Register another handler for the same path
        def another_dummy(**kwargs):
            return "changed"

        router.add_route(path, "GET", another_dummy)
        # Routes count should not increase
        assert len(router.routes) == initial_routes
        expected_pattern = re.sub(r"{(\w+)}", r"(?P<\1>[^/]+)", path)
        expected_full_pattern = expected_pattern + "$"
        # Check GET method handler was updated to another_dummy
        assert router._endpoint_map[expected_pattern]["GET"] == another_dummy
        # Check regex pattern remains unchanged
        actual_pattern = router.routes[-1].matcher.regex.pattern
        assert actual_pattern == expected_full_pattern

    def test_add_route_with_app_none(self, router_without_app):
        """
        Test adding a route when app is None:
        - Should add to routes list
        - Should not try to register with app (would throw error if attempted)
        - This specifically targets lines 120-121 in the add_route method
        """
        path = "/test/{id}"
        initial_routes = len(router_without_app.routes)
        router_without_app.add_route(path, "GET", dummy_endpoint)

        # Routes count should increase
        assert len(router_without_app.routes) == initial_routes + 1
        # Path should be registered in endpoint map
        expected_pattern = re.sub(r"{(\w+)}", r"(?P<\1>[^/]+)", path)
        assert expected_pattern in router_without_app._endpoint_map
        assert (
            router_without_app._endpoint_map[expected_pattern]["GET"] == dummy_endpoint
        )

        # For line coverage of 120-121:
        # Get the rule that was just added
        rule = router_without_app.routes[0]
        # Ensure it has the correct pattern and kwargs
        assert rule.matcher.regex.pattern == expected_pattern + "$"
        assert "endpoints" in rule.target_kwargs
        assert "router" in rule.target_kwargs
        assert rule.target_kwargs["endpoints"] == {"GET": dummy_endpoint}

    def test_add_route_with_app_registered_path(self, router_without_app):
        """Test adding another method to an already registered path when app is None."""
        # First, add one route
        path = "/test/{id}"
        router_without_app.add_route(path, "GET", dummy_endpoint)

        # Then, add another method for the same path
        def post_endpoint(**kwargs):
            return "post"

        initial_routes = len(router_without_app.routes)
        router_without_app.add_route(path, "POST", post_endpoint)

        # Routes count should not increase
        assert len(router_without_app.routes) == initial_routes

        # Both methods should be registered
        expected_pattern = re.sub(r"{(\w+)}", r"(?P<\1>[^/]+)", path)
        assert "GET" in router_without_app._endpoint_map[expected_pattern]
        assert "POST" in router_without_app._endpoint_map[expected_pattern]
        assert (
            router_without_app._endpoint_map[expected_pattern]["GET"] == dummy_endpoint
        )
        assert (
            router_without_app._endpoint_map[expected_pattern]["POST"] == post_endpoint
        )

    def test_register_docs_endpoints(self, router):
        """
        Test _register_docs_endpoints method:
        - Should add 3 documentation routes to routes list
        - If app is not None, should call app.add_handlers with 3 handlers
        """
        # Clear routes list
        router.routes = []
        called_handlers = []

        def fake_add_handlers(host_pattern, handlers):
            called_handlers.extend(handlers)

        router.app.add_handlers = fake_add_handlers
        # Set URLs for documentation endpoints
        router.openapi_url = "/openapi.json"
        router.docs_url = "/docs"
        router.redoc_url = "/redoc"
        router._register_docs_endpoints()
        # Check exactly 3 routes were added
        assert len(router.routes) == 3
        # Check fake_add_handlers was called with 3 handlers
        assert len(called_handlers) == 3
        # Check route names match documentation endpoints
        names = {r.name for r in router.routes}
        assert "openapi-schema" in names
        assert "swagger-ui" in names
        assert "redoc-ui" in names

    def test_register_docs_endpoints_without_app(self, router_without_app):
        """
        Test _register_docs_endpoints when app is None:
        - Should still add 3 routes to routes list
        - Should not try to register with app (would throw error if attempted)
        """
        # Clear routes list
        router_without_app.routes = []
        # Set URLs for documentation endpoints
        router_without_app.openapi_url = "/openapi.json"
        router_without_app.docs_url = "/docs"
        router_without_app.redoc_url = "/redoc"
        router_without_app._register_docs_endpoints()

        # Check exactly 3 routes were added
        assert len(router_without_app.routes) == 3
        # Check route names match documentation endpoints
        names = {r.name for r in router_without_app.routes}
        assert "openapi-schema" in names
        assert "swagger-ui" in names
        assert "redoc-ui" in names
