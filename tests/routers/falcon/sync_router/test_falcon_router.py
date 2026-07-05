from falcon import App
from pydantic import BaseModel

from fastopenapi.routers import FalconRouter


class TestFalconRouter:

    def test_router_initialization(self):
        """Test router initialization"""
        app = App()
        router = FalconRouter(
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
        app = App()
        router = FalconRouter(app=app)

        def test_endpoint():
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
        app = App()
        main_router = FalconRouter(app=app)
        sub_router = FalconRouter()

        def sub_endpoint():
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
        app = App()
        router = FalconRouter(
            app=app,
            title="Test API",
            description="Test Description",
            version="1.0.0",
        )

        class TestModel(BaseModel):
            id: int
            name: str

        @router.get("/test/{id}", response_model=TestModel)
        def get_test(id: int):
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


class TestCopyFalconResponse:
    """User-returned falcon.Response objects are copied faithfully"""

    def _copy(self, source):
        import falcon

        router = FalconRouter()
        target = falcon.Response()
        router._copy_falcon_response(source, target)
        return target

    def test_copies_media(self):
        import falcon

        source = falcon.Response()
        source.status = 201
        source.media = {"a": 1}
        source.set_header("X-Custom", "yes")

        target = self._copy(source)

        assert target.status == source.status
        assert target.media == {"a": 1}
        assert target.get_header("X-Custom") == "yes"

    def test_copies_text(self):
        import falcon

        source = falcon.Response()
        source.text = "hello"
        source.content_type = "text/plain"

        target = self._copy(source)

        assert target.text == "hello"
        assert target.content_type == "text/plain"

    def test_copies_data(self):
        import falcon

        source = falcon.Response()
        source.data = b"\x01\x02"

        target = self._copy(source)

        assert target.data == b"\x01\x02"


class TestFalconAsyncGuard:
    def test_async_endpoint_rejected_at_registration(self):
        """Async endpoints are rejected at registration time"""
        import pytest

        router = FalconRouter()

        with pytest.raises(TypeError) as excinfo:

            @router.get("/items-async")
            async def get_items_async():
                return []

        err_msg = (
            "Async endpoint 'get_items_async' cannot be used with sync router. "
            "Use FalconAsyncRouter for async support."
        )
        assert err_msg in str(excinfo.value)


class TestNativeFalconResponse:
    def test_endpoint_returning_falcon_response(self):
        """A user-returned falcon.Response passes through untouched"""
        import falcon
        import falcon.testing

        from fastopenapi import Header

        app = App()
        router = FalconRouter(app=app)

        @router.get("/native")
        def native(x_request_id: str = Header(None)):
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


class TestFalconAutoHead:
    def test_explicit_head_before_get_wins(self):
        import falcon.testing

        app = App()
        router = FalconRouter(app=app)

        @router.head("/h")
        def explicit_head():
            return None, 200, {"X-From": "explicit"}

        @router.get("/h")
        def get_endpoint():
            return {"ok": True}

        client = falcon.testing.TestClient(app)
        result = client.simulate_head("/h")

        assert result.status_code == 200
        assert result.headers.get("X-From") == "explicit"

    def test_copy_empty_falcon_response(self):
        import falcon

        router = FalconRouter()
        source = falcon.Response()
        source.set_header("X-Only-Headers", "1")
        target = falcon.Response()

        router._copy_falcon_response(source, target)

        assert target.get_header("X-Only-Headers") == "1"
        assert target.media is None
        assert target.text is None
        assert target.data is None
