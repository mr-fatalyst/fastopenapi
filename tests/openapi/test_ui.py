from fastopenapi.core.constants import REDOC_URL, SWAGGER_URL
from fastopenapi.openapi.ui import render_redoc_ui, render_swagger_ui


class TestUI:
    def test_render_swagger_ui(self):
        # Test rendering Swagger UI HTML
        html = render_swagger_ui("/api/openapi.json")

        assert "<!DOCTYPE html>" in html
        assert SWAGGER_URL in html
        assert "url: '/api/openapi.json'" in html
        assert "dom_id: '#swagger-ui'" in html

    def test_render_redoc_ui(self):
        # Test rendering ReDoc UI HTML
        html = render_redoc_ui("/api/openapi.json")

        assert "<!DOCTYPE html>" in html
        assert REDOC_URL in html
        assert "spec-url='/api/openapi.json'" in html
