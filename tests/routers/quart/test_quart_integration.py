import pytest
from pydantic_core import to_json


class TestQuartIntegration:

    @pytest.mark.asyncio
    async def test_get_items(self, client):
        """Test fetching all items"""
        response = await client.get("/items")

        assert response.status_code == 200
        result = await response.get_json()
        assert len(result) == 2
        assert result[0]["name"] == "Item 1"
        assert result[1]["name"] == "Item 2"

    @pytest.mark.asyncio
    async def test_get_items_invalid(self, client):
        """Test fetching all items invalid"""
        response = await client.get("/items-invalid")

        assert response.status_code == 500
        result = await response.get_json()
        assert result["error"]["message"] == "Incorrect response type"

    @pytest.mark.asyncio
    async def test_get_items_fail(self, client):
        """Test fetching all items with an error"""
        response = await client.get("/items-fail")

        assert response.status_code == 500
        result = await response.get_json()
        assert result["error"]["message"] == "TEST ERROR"

    @pytest.mark.asyncio
    async def test_get_item(self, client):
        """Test fetching an item by ID"""
        response = await client.get("/items/1")

        assert response.status_code == 200
        result = await response.get_json()
        assert result["id"] == 1
        assert result["name"] == "Item 1"
        assert result["description"] == "Description 1"

    @pytest.mark.asyncio
    async def test_get_item_bad_request(self, client):
        """Test fetching an item with an incorrect ID type"""
        response = await client.get("/items/abc")

        assert response.status_code == 400
        result = await response.get_json()
        assert result["error"]["message"] == ("Error parsing parameter 'item_id'")

    @pytest.mark.asyncio
    async def test_get_nonexistent_item(self, client):
        """Test fetching a nonexistent item"""
        response = await client.get("/items/999")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_item(self, client):
        """Test creating an item"""
        new_item = {"name": "New Item", "description": "New Description"}
        response = await client.post(
            "/items",
            data=to_json(new_item).decode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 201
        result = await response.get_json()
        assert result["id"] == 3
        assert result["name"] == "New Item"
        assert result["description"] == "New Description"

    @pytest.mark.asyncio
    async def test_create_item_incorrect(self, client):
        """Test creating an item with an incorrect body"""
        new_item = {"name": None, "description": "New Description"}
        response = await client.post(
            "/items",
            data=to_json(new_item).decode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422
        result = await response.get_json()
        assert "Validation error for parameter" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_create_item_invalid_json(self, client):
        """Test creating an item with invalid JSON"""
        response = await client.post(
            "/items",
            data="incorrect json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422
        result = await response.get_json()
        assert "Validation error for parameter" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_update_item(self, client):
        """Test updating an item"""
        update_data = {"name": "Updated Item", "description": "Updated Description"}
        response = await client.put(
            "/items/2",
            data=to_json(update_data).decode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        result = await response.get_json()
        assert result["id"] == 2
        assert result["name"] == "Updated Item"
        assert result["description"] == "Updated Description"

    @pytest.mark.asyncio
    async def test_delete_item(self, client):
        """Test deleting an item"""
        response = await client.delete("/items/1")

        assert response.status_code == 204

        # Verify that the item has actually been deleted
        response = await client.get("/items/1")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_openapi_schema_endpoint(self, client):
        """Test OpenAPI schema endpoint"""
        response = await client.get("/openapi.json")

        assert response.status_code == 200
        schema = await response.get_json()
        assert schema["info"]["title"] == "Test API"
        assert "/items" in schema["paths"]
        assert "/items/{item_id}" in schema["paths"]

    @pytest.mark.asyncio
    async def test_swagger_ui_endpoint(self, client):
        """Test Swagger UI endpoint"""
        response = await client.get("/docs")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        data = await response.data
        html_text = data.decode()
        assert "swagger-ui" in html_text

    @pytest.mark.asyncio
    async def test_redoc_ui_endpoint(self, client):
        """Test ReDoc UI endpoint"""
        response = await client.get("/redoc")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        data = await response.data
        html_text = data.decode()
        assert "redoc" in html_text

    @pytest.mark.asyncio
    async def test_query_parameters_handling(self, client):
        """Test handling of query parameters"""
        # Test with a single value parameter
        response = await client.get("/list-test?param1=single_value")
        assert response.status_code == 200
        data = await response.get_json()
        assert data["received_param1"] == "single_value"

        # Test with a parameter that has multiple values
        response = await client.get(
            "/list-test?param1=first_value&param2=value1&param2=value2"
        )
        assert response.status_code == 200
        data = await response.get_json()
        assert data["received_param1"] == "first_value"
        assert isinstance(data["received_param2"], list)
        assert data["received_param2"] == ["value1", "value2"]

    @pytest.mark.asyncio
    async def test_binary_response(self, client):
        """Test binary content response"""
        response = await client.get("/test-binary")
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "application/octet-stream"
        data = await response.data
        assert isinstance(data, bytes)
        assert data == b"\x00\x01\x02\x03\x04"

    @pytest.mark.asyncio
    async def test_image_response(self, client):
        """Test image binary response"""
        response = await client.get("/test-image")
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "image/png"
        data = await response.data
        assert isinstance(data, bytes)

    @pytest.mark.asyncio
    async def test_csv_response(self, client):
        """Test CSV text response"""
        response = await client.get("/test-csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers["Content-Type"]
        data = await response.data
        text = data.decode("utf-8")
        assert "name,age,city" in text
        assert "John,30,NYC" in text

    @pytest.mark.asyncio
    async def test_xml_response(self, client):
        """Test XML text response"""
        response = await client.get("/test-xml")
        assert response.status_code == 200
        assert "application/xml" in response.headers["Content-Type"]
        data = await response.data
        text = data.decode("utf-8")
        assert "<root>" in text
        assert "<item>value</item>" in text

    @pytest.mark.asyncio
    async def test_plain_text_response(self, client):
        """Test plain text response"""
        response = await client.get("/test-text")
        assert response.status_code == 200
        assert "text/plain" in response.headers["Content-Type"]
        data = await response.data
        text = data.decode("utf-8")
        assert text == "Hello, World!"

    @pytest.mark.asyncio
    async def test_html_response(self, client):
        """Test HTML text response"""
        response = await client.get("/test-html")
        assert response.status_code == 200
        assert "text/html" in response.headers["Content-Type"]
        data = await response.data
        text = data.decode("utf-8")
        assert "<html>" in text
        assert "<body>" in text

    @pytest.mark.asyncio
    async def test_custom_headers_in_response(self, client):
        """Test custom headers are preserved"""
        response = await client.get("/test-custom-headers")
        assert response.status_code == 200
        assert response.headers["X-Custom-Header"] == "CustomValue"
        assert response.headers["X-Request-ID"] == "12345"

    @pytest.mark.asyncio
    async def test_pdf_response(self, client):
        """Test PDF binary response"""
        response = await client.get("/test-pdf")
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "application/pdf"
        data = await response.data
        assert isinstance(data, bytes)
        assert data.startswith(b"%PDF")
