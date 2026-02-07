from pydantic import BaseModel
from sanic import Sanic

from fastopenapi.routers import SanicRouter


class TestSanicRouter:
    def test_router_initialization(self):
        """Test router initialization"""
        app = Sanic("SanicTestApp")
        router = SanicRouter(
            app=app,
            title="Test API",
            description="Test API Description",
            version="1.0.0",
        )
        assert router.title == "Test API"
        assert router.description == "Test API Description"
        assert router.version == "1.0.0"
        assert router.app == app

    def test_add_route(self):
        """Test adding a route"""
        app = Sanic("SanicTestApp")
        router = SanicRouter(app=app)

        async def test_endpoint():
            return {"message": "Test"}

        router.add_route("/test", "GET", test_endpoint)
        routes = router.get_routes()

        assert len(routes) == 1
        route = routes[0]
        assert route.path == "/test"
        assert route.method == "GET"
        assert route.endpoint == test_endpoint

        # Check if the route exists in the Sanic app
        route_found = False
        for route in app.router.routes:
            if route.uri == "/test" and "GET" in route.methods:
                route_found = True
                break
        assert route_found

    def test_include_router(self):
        """Test including another router"""
        app = Sanic("SanicTestApp")
        main_router = SanicRouter(app=app)
        sub_router = SanicRouter()

        async def sub_endpoint():
            return {"message": "Sub"}

        sub_router.add_route("/sub", "GET", sub_endpoint)
        main_router.include_router(sub_router, prefix="/api")

        routes = main_router.get_routes()
        assert len(routes) == 1
        route = routes[0]
        assert route.path == "/api/sub"
        assert route.method == "GET"
        assert route.endpoint == sub_endpoint

        # Check if the route exists in the Sanic app
        route_found = False
        for route in app.router.routes:
            if route.uri == "/api/sub" and "GET" in route.methods:
                route_found = True
                break
        assert route_found

    def test_openapi_generation(self):
        """Test OpenAPI schema generation"""
        app = Sanic("SanicTestApp")
        router = SanicRouter(
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
        assert schema["paths"]["/test/{id}"]["get"]["summary"] == "Get Test"
        assert "TestModel" in schema["components"]["schemas"]
