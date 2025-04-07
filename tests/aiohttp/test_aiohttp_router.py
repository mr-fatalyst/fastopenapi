import functools

from aiohttp import web
from pydantic import BaseModel

from fastopenapi.routers import AioHttpRouter


class TestAioHttpRouter:
    def test_router_initialization(self):
        """Test router initialization"""
        app = web.Application()
        router = AioHttpRouter(
            app=app,
            title="Test API",
            description="Test API Description",
            version="1.0.0",
        )
        assert router.title == "Test API"
        assert router.description == "Test API Description"
        assert router.version == "1.0.0"
        assert router.app == app

    def test_add_route(self, event_loop):
        """Test adding a route"""
        app = web.Application()
        router = AioHttpRouter(app=app)

        async def test_endpoint():
            return {"message": "Test"}

        router.add_route("/test", "GET", test_endpoint)
        routes = [
            route
            for route in app.router.routes()
            if route.resource.get_info().get("path") == "/test"
        ]
        assert len(routes) == 1

    def test_include_router(self, event_loop):
        """Test including a sub-router"""
        app = web.Application()
        main_router = AioHttpRouter(app=app)
        sub_router = AioHttpRouter()

        async def sub_endpoint():
            return {"message": "Sub"}

        sub_router.add_route("/sub", "GET", sub_endpoint)
        main_router.include_router(sub_router, prefix="/api")
        routes = [
            route
            for route in app.router.routes()
            if route.resource.get_info().get("path") == "/api/sub"
        ]
        assert len(routes) == 1

    def test_add_route_app_none(self, dummy_endpoint):
        """
        Verify that if the application is not passed (app=None),
        then calling add_route stores the route in the internal _routes_aiohttp list.
        """
        router = AioHttpRouter(
            app=None,
            openapi_url="/openapi.json",
            docs_url="/docs",
            redoc_url="/redoc",
            title="Test API",
            version="1.0.0",
        )
        router.add_route("/test", "GET", dummy_endpoint)
        # Verify that the route is not registered in app.router
        # but is saved in the internal list
        assert len(router._routes_aiohttp) == 1
        path, method, view = router._routes_aiohttp[0]
        assert path == "/test"
        assert method.upper() == "GET"
        # Verify that view is a functools.partial with the correct parameters
        assert isinstance(view, functools.partial)
        # Optionally verify that the partial contains the correct router and endpoint
        assert view.keywords.get("router") is router
        assert view.keywords.get("endpoint") is dummy_endpoint

    def test_register_docs_endpoints_app_none(self):
        """
        Verify that if the application is not passed (app=None),
        then the _register_docs_endpoints method does not register documentation routes.
        """
        router = AioHttpRouter(
            app=None,
            openapi_url="/openapi.json",
            docs_url="/docs",
            redoc_url="/redoc",
            title="Test API",
            version="1.0.0",
        )
        # Call _register_docs_endpoints and make sure
        # nothing happens (no exception is thrown)
        result = router._register_docs_endpoints()
        assert result is None

    def test_openapi_generation(self):
        """Test OpenAPI schema generation"""
        app = web.Application()
        router = AioHttpRouter(
            app=app,
            title="Test API",
            description="Test Description",
            version="1.0.0",
        )

        class TestModel(BaseModel):
            id: int
            name: str

        @router.get("/test/{id}", response_model=TestModel)
        async def get_test(id: int):
            """Test endpoint"""
            return TestModel(id=id, name="Test")

        schema = router.openapi
        assert schema["info"]["title"] == "Test API"
        assert schema["info"]["version"] == "1.0.0"
        assert schema["info"]["description"] == "Test Description"
        assert "/test/{id}" in schema["paths"]
        assert "get" in schema["paths"]["/test/{id}"]
        assert schema["paths"]["/test/{id}"]["get"]["summary"] == "Test endpoint"
        assert "TestModel" in schema["components"]["schemas"]
