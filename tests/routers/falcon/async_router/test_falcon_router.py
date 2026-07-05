import falcon.asgi
from pydantic import BaseModel

from fastopenapi.routers import FalconAsyncRouter


class TestFalconAsyncRouter:

    def test_router_initialization(self):
        """Test router initialization"""
        app = falcon.asgi.App()
        router = FalconAsyncRouter(
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
        app = falcon.asgi.App()
        router = FalconAsyncRouter(app=app)

        async def test_endpoint():
            return {"message": "Test"}

        router.add_route("/test", "GET", test_endpoint)
        routes = router.get_routes()

        assert len(routes) == 1
        route = routes[0]
        assert route.path == "/test"
        assert route.method == "GET"
        assert route.endpoint == test_endpoint
        assert "/test" in router._resources

    def test_include_router(self):
        """Test including another router"""
        app = falcon.asgi.App()
        main_router = FalconAsyncRouter(app=app)
        sub_router = FalconAsyncRouter()

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

    def test_openapi_generation(self):
        """Test OpenAPI schema generation"""
        app = falcon.asgi.App()
        router = FalconAsyncRouter(
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


class TestNativeFalconResponseAsync:
    def test_endpoint_returning_falcon_response(self):
        """A user-returned falcon.Response passes through untouched"""
        import falcon
        import falcon.asgi
        import falcon.testing

        from fastopenapi import Header

        app = falcon.asgi.App()
        router = FalconAsyncRouter(app=app)

        @router.get("/native")
        async def native(x_request_id: str = Header(None)):
            resp = falcon.Response()
            resp.media = {"received": x_request_id or "none"}
            resp.status = 200
            resp.set_header("X-Echo-Id", x_request_id or "none")
            return resp

        client = falcon.testing.TestClient(app)
        result = client.simulate_get("/native", headers={"X-Request-Id": "trace-9"})

        assert result.status_code == 200
        assert result.json == {"received": "trace-9"}
        assert result.headers.get("X-Echo-Id") == "trace-9"
