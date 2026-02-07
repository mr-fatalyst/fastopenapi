import pytest
from pydantic_core import from_json, to_json


class TestSanicIntegration:

    @pytest.mark.asyncio
    async def test_get_items(self, client):
        """Test fetching all items"""
        _, response = await client.get("/items")

        assert response.status_code == 200
        result = from_json(response.text)
        assert len(result) == 2
        assert result[0]["name"] == "Item 1"
        assert result[1]["name"] == "Item 2"

    @pytest.mark.asyncio
    async def test_get_items_invalid(self, client):
        """Test fetching all items invalid"""
        _, response = await client.get("/items-invalid")

        assert response.status_code == 500
        result = from_json(response.text)
        assert result["error"]["message"] == "Incorrect response type"

    def test_get_items_sync(self, sync_client):
        """Test fetching all items"""
        _, response = sync_client.get("/items-sync")

        assert response.status_code == 200
        result = from_json(response.text)
        assert len(result) == 2
        assert result[0]["name"] == "Item 1"
        assert result[1]["name"] == "Item 2"

    @pytest.mark.asyncio
    async def test_get_items_fail(self, client):
        """Test fetching all items with an error"""
        _, response = await client.get("/items-fail")

        assert response.status_code == 500
        result = from_json(response.text)
        assert result["error"]["message"] == "TEST ERROR"

    @pytest.mark.asyncio
    async def test_get_item(self, client):
        """Test fetching an item by ID"""
        _, response = await client.get("/items/1")

        assert response.status_code == 200
        result = from_json(response.text)
        assert result["id"] == 1
        assert result["name"] == "Item 1"
        assert result["description"] == "Description 1"

    @pytest.mark.asyncio
    async def test_get_item_bad_request(self, client):
        """Test fetching an item with an incorrect ID type"""
        _, response = await client.get("/items/abc")

        assert response.status_code == 422
        result = from_json(response.text)
        assert result["error"]["message"] == ("Error parsing parameter 'item_id'")

    @pytest.mark.asyncio
    async def test_get_nonexistent_item(self, client):
        """Test fetching a nonexistent item"""
        _, response = await client.get("/items/999")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_item(self, client):
        """Test creating an item"""
        new_item = {"name": "New Item", "description": "New Description"}
        _, response = await client.post(
            "/items",
            data=to_json(new_item).decode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 201
        result = from_json(response.text)
        assert result["id"] == 3
        assert result["name"] == "New Item"
        assert result["description"] == "New Description"

    @pytest.mark.asyncio
    async def test_create_item_incorrect(self, client):
        """Test creating an item with an incorrect body"""
        new_item = {"name": None, "description": "New Description"}
        _, response = await client.post(
            "/items",
            data=to_json(new_item).decode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422
        result = from_json(response.text)
        assert "Validation error for parameter" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_create_item_invalid_json(self, client):
        """Test creating an item with invalid JSON"""
        _, response = await client.post(
            "/items",
            data="incorrect json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_item(self, client):
        """Test updating an item"""
        update_data = {"name": "Updated Item", "description": "Updated Description"}
        _, response = await client.put(
            "/items/2",
            data=to_json(update_data).decode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        result = from_json(response.text)
        assert result["id"] == 2
        assert result["name"] == "Updated Item"
        assert result["description"] == "Updated Description"

    @pytest.mark.asyncio
    async def test_delete_item(self, client):
        """Test deleting an item"""
        _, response = await client.delete("/items/1")

        assert response.status_code == 204

        # Verify that the item has actually been deleted
        _, response = await client.get("/items/1")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_openapi_schema_endpoint(self, client):
        """Test OpenAPI schema endpoint"""
        _, response = await client.get("/openapi.json")

        assert response.status_code == 200
        schema = from_json(response.text)
        assert schema["info"]["title"] == "Test API"
        assert "/items" in schema["paths"]
        assert "/items/{item_id}" in schema["paths"]

    @pytest.mark.asyncio
    async def test_swagger_ui_endpoint(self, client):
        """Test Swagger UI endpoint"""
        _, response = await client.get("/docs")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        html_text = response.text
        assert "swagger-ui" in html_text

    @pytest.mark.asyncio
    async def test_redoc_ui_endpoint(self, client):
        """Test ReDoc UI endpoint"""
        _, response = await client.get("/redoc")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        html_text = response.text
        assert "redoc" in html_text

    @pytest.mark.asyncio
    async def test_query_parameter_processing(self, client):
        """Test handling of query parameters"""
        # Test case 1: Single parameter with a single value
        _, response = await client.get("/echo?param=value")
        assert response.status == 200
        assert response.json["param"] == "value"

        # Test case 2: Single parameter with multiple values
        _, response = await client.get("/echo?param2=value1&param2=value2")
        assert response.status == 200
        assert isinstance(response.json["param2"], list)
        assert response.json["param2"] == ["value1", "value2"]

        # Test case 3: Multiple parameters with mixed value counts
        _, response = await client.get("/echo?param=value&param2=value1&param2=value2")
        assert response.status == 200
        assert response.json["param"] == "value"
        assert isinstance(response.json["param2"], list)
        assert response.json["param2"] == ["value1", "value2"]

        # Test case 4: Parameter with special characters
        _, response = await client.get("/echo?param=hello%20world")
        assert response.status == 200
        assert response.json["param"] == "hello world"

    @pytest.mark.asyncio
    async def test_binary_response(self, client):
        """Test binary content response"""
        _, response = await client.get("/test-binary")
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "application/octet-stream"
        assert isinstance(response.body, bytes)
        assert response.body == b"\x00\x01\x02\x03\x04"

    @pytest.mark.asyncio
    async def test_image_response(self, client):
        """Test image binary response"""
        _, response = await client.get("/test-image")
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "image/png"
        assert isinstance(response.body, bytes)

    @pytest.mark.asyncio
    async def test_csv_response(self, client):
        """Test CSV text response"""
        _, response = await client.get("/test-csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers["Content-Type"]
        assert "name,age,city" in response.text
        assert "John,30,NYC" in response.text

    @pytest.mark.asyncio
    async def test_xml_response(self, client):
        """Test XML text response"""
        _, response = await client.get("/test-xml")
        assert response.status_code == 200
        assert "application/xml" in response.headers["Content-Type"]
        assert "<root>" in response.text
        assert "<item>value</item>" in response.text

    @pytest.mark.asyncio
    async def test_plain_text_response(self, client):
        """Test plain text response"""
        _, response = await client.get("/test-text")
        assert response.status_code == 200
        assert "text/plain" in response.headers["Content-Type"]
        assert response.text == "Hello, World!"

    @pytest.mark.asyncio
    async def test_html_response(self, client):
        """Test HTML text response"""
        _, response = await client.get("/test-html")
        assert response.status_code == 200
        assert "text/html" in response.headers["Content-Type"]
        assert "<html>" in response.text
        assert "<body>" in response.text

    @pytest.mark.asyncio
    async def test_custom_headers_in_response(self, client):
        """Test custom headers are preserved"""
        _, response = await client.get("/test-custom-headers")
        assert response.status_code == 200
        assert response.headers["X-Custom-Header"] == "CustomValue"
        assert response.headers["X-Request-ID"] == "12345"

    @pytest.mark.asyncio
    async def test_pdf_response(self, client):
        """Test PDF binary response"""
        _, response = await client.get("/test-pdf")
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "application/pdf"
        assert isinstance(response.body, bytes)
        assert response.body.startswith(b"%PDF")
