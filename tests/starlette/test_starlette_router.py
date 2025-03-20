from pydantic import BaseModel
from starlette.applications import Starlette

from fastopenapi.routers import StarletteRouter


class TestStarletteRouter:

    def test_router_initialization(self):
        """Test router initialization"""
        app = Starlette()
        router = StarletteRouter(
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
        app = Starlette()
        router = StarletteRouter(app=app)

        async def test_endpoint():
            return {"message": "Test"}

        router.add_route("/test", "GET", test_endpoint)
        routes = router.get_routes()

        assert len(routes) == 1
        assert routes[0] == ("/test", "GET", test_endpoint)
        assert "/test" in {i for i, _, _ in router._routes}

    def test_include_router(self):
        """Test including another router"""
        app = Starlette()
        main_router = StarletteRouter(app=app)
        sub_router = StarletteRouter()

        async def sub_endpoint():
            return {"message": "Sub"}

        sub_router.add_route("/sub", "GET", sub_endpoint)
        main_router.include_router(sub_router, prefix="/api")

        routes = main_router.get_routes()
        assert len(routes) == 1
        assert routes[0][0] == "/api/sub"
        assert routes[0][1] == "GET"

    def test_openapi_generation(self):
        """Test OpenAPI schema generation"""
        app = Starlette()
        router = StarletteRouter(
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
