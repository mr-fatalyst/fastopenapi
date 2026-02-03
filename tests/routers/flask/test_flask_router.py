from flask import Blueprint, Flask
from pydantic import BaseModel

from fastopenapi.routers import FlaskRouter


class TestFlaskRouter:

    def test_router_initialization(self):
        """Test router initialization"""
        app = Flask(__name__)
        router = FlaskRouter(
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
        app = Flask(__name__)
        router = FlaskRouter(app=app)

        async def test_endpoint():
            return {"message": "Test"}

        router.add_route("/test", "GET", test_endpoint)
        routes = router.get_routes()

        assert len(routes) == 1
        route = routes[0]
        assert route.path == "/test"
        assert route.method == "GET"
        assert route.endpoint == test_endpoint
        assert "test_endpoint:GET:/test" in router.app.view_functions

    def test_include_router(self):
        """Test including another router"""
        app = Flask(__name__)
        main_router = FlaskRouter(app=app)
        sub_router = FlaskRouter()

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
        app = Flask(__name__)
        router = FlaskRouter(
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

    def test_router_initialization_with_blueprint(self):
        """Test router initialization with Blueprint"""
        app = Flask(__name__)
        bp = Blueprint("api", __name__, url_prefix="/api")

        router = FlaskRouter(
            app=app,
            blueprint=bp,
            title="Test API",
            description="Test API Description",
            version="1.0.0",
        )

        assert router.title == "Test API"
        assert router.description == "Test API Description"
        assert router.version == "1.0.0"
        assert router.app == app
        assert router.blueprint == bp

    def test_add_route_to_blueprint(self):
        """Test adding a route to Blueprint instead of app"""
        app = Flask(__name__)
        bp = Blueprint("api", __name__, url_prefix="/api")
        router = FlaskRouter(app=app, blueprint=bp)

        @router.get("/test")
        def test_endpoint():
            return {"message": "Test"}

        routes = router.get_routes()

        # Route should be registered in router
        assert len(routes) == 1
        route = routes[0]
        assert route.path == "/test"
        assert route.method == "GET"
        assert route.endpoint == test_endpoint

        # Register blueprint with app to verify registration
        app.register_blueprint(bp)

        # After registration, verify the route works
        with app.test_client() as client:
            response = client.get("/api/test")
            assert response.status_code == 200
            data = response.get_json()
            assert data["message"] == "Test"

    def test_blueprint_fallback_to_app(self):
        """Test that router falls back to app when blueprint is None"""
        app = Flask(__name__)
        router = FlaskRouter(app=app, blueprint=None)

        @router.get("/test")
        def test_endpoint():
            return {"message": "Test"}

        # Test the route works directly on app
        with app.test_client() as client:
            response = client.get("/test")
            assert response.status_code == 200
            data = response.get_json()
            assert data["message"] == "Test"

    def test_docs_endpoints_on_blueprint(self):
        """Test that documentation endpoints are registered on blueprint"""
        app = Flask(__name__)
        bp = Blueprint("api", __name__, url_prefix="/api")
        router = FlaskRouter(app=app, blueprint=bp)

        # Register blueprint with app
        app.register_blueprint(bp)

        # Test that docs endpoints are accessible through blueprint
        with app.test_client() as client:
            # Test OpenAPI JSON endpoint
            response = client.get("/api/openapi.json")
            assert response.status_code == 200

            # Test Swagger UI endpoint
            response = client.get("/api/docs")
            assert response.status_code == 200
            assert b"html" in response.data.lower()

            # Test ReDoc UI endpoint
            response = client.get("/api/redoc")
            assert response.status_code == 200
            assert b"html" in response.data.lower()

    def test_blueprint_integration_with_app(self):
        """Test that blueprint with registered routes works with Flask app"""
        app = Flask(__name__)
        bp = Blueprint("api", __name__, url_prefix="/api")

        class ItemResponse(BaseModel):
            id: int
            name: str

        router = FlaskRouter(app=app, blueprint=bp)

        @router.get("/items/{item_id}", response_model=ItemResponse)
        def get_item(item_id: int):
            """Get an item by ID"""
            return ItemResponse(id=item_id, name=f"Item {item_id}")

        # Register blueprint with app
        app.register_blueprint(bp)

        # Test the route
        with app.test_client() as client:
            response = client.get("/api/items/123")
            assert response.status_code == 200
            data = response.get_json()
            assert data["id"] == 123
            assert data["name"] == "Item 123"

    def test_openapi_generation_with_blueprint(self):
        """Test OpenAPI schema generation with blueprint"""
        app = Flask(__name__)
        bp = Blueprint("api", __name__, url_prefix="/api")

        router = FlaskRouter(
            app=app,
            blueprint=bp,
            title="Blueprint API",
            description="API with Blueprint",
            version="2.0.0",
        )

        class TestModel(BaseModel):
            id: int
            name: str

        @router.get("/test/{id}", response_model=TestModel)
        def get_test(id: int):
            """Test endpoint with blueprint"""
            return TestModel(id=id, name="Blueprint Test")

        schema = router.openapi

        assert schema["info"]["title"] == "Blueprint API"
        assert schema["info"]["version"] == "2.0.0"
        assert schema["info"]["description"] == "API with Blueprint"
        assert "/test/{id}" in schema["paths"]
        assert "get" in schema["paths"]["/test/{id}"]
        assert schema["paths"]["/test/{id}"]["get"]["summary"] == "Test endpoint with blueprint"
