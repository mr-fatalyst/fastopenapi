import json

import pytest


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
    async def test_get_items_fail(self, client):
        """Test fetching all items with an error"""
        response = await client.get("/items-fail")

        assert response.status_code == 500
        result = await response.get_json()
        assert result["detail"] == "TEST ERROR"

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
    async def test_get_item_unprocessable(self, client):
        """Test fetching an item with an incorrect ID type"""
        response = await client.get("/items/abc")

        assert response.status_code == 422
        result = await response.get_json()
        assert result["detail"] == (
            "Error casting parameter 'item_id' to <class 'int'>: "
            "invalid literal for int() with base 10: 'abc'"
        )

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
            data=json.dumps(new_item),
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
            data=json.dumps(new_item),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422
        result = await response.get_json()
        assert "Validation error for parameter" in result["detail"]

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
        assert "Validation error for parameter" in result["detail"]

    @pytest.mark.asyncio
    async def test_update_item(self, client):
        """Test updating an item"""
        update_data = {"name": "Updated Item", "description": "Updated Description"}
        response = await client.put(
            "/items/2",
            data=json.dumps(update_data),
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
