import pytest
from pydantic_core import to_json


class TestAioHttpIntegration:
    @pytest.mark.asyncio
    async def test_get_items(self, client):
        """Test retrieving all items"""
        resp = await client.get("/items")
        assert resp.status == 200
        data = await resp.json()
        assert len(data) == 2
        assert data[0]["name"] == "Item 1"
        assert data[1]["name"] == "Item 2"

    @pytest.mark.asyncio
    async def test_get_items_sync(self, client):
        """Test retrieving all items (synchronous endpoint)"""
        resp = await client.get("/items-sync")
        assert resp.status == 200
        data = await resp.json()
        assert len(data) == 2
        assert data[0]["name"] == "Item 1"
        assert data[1]["name"] == "Item 2"

    @pytest.mark.asyncio
    async def test_get_items_fail(self, client):
        """Test retrieving items with generated error"""
        resp = await client.get("/items-fail")
        assert resp.status == 500
        data = await resp.json()
        assert data["error"]["message"] == "TEST ERROR"

    @pytest.mark.asyncio
    async def test_get_item(self, client):
        """Test retrieving item by ID"""
        resp = await client.get("/items/1")
        assert resp.status == 200
        data = await resp.json()
        assert data["id"] == 1
        assert data["name"] == "Item 1"
        assert data["description"] == "Description 1"

    @pytest.mark.asyncio
    async def test_get_item_bad_request(self, client):
        """Test retrieving item with incorrect parameter type"""
        resp = await client.get("/items/abc")
        assert resp.status == 400
        data = await resp.json()
        assert "Error parsing parameter" in data["error"]["message"]

    @pytest.mark.asyncio
    async def test_get_nonexistent_item(self, client):
        """Test retrieving non-existent item"""
        resp = await client.get("/items/999")
        assert resp.status == 404

    @pytest.mark.asyncio
    async def test_create_item(self, client):
        """Test creating an item"""
        new_item = {"name": "New Item", "description": "New Description"}
        headers = {"Content-Type": "application/json"}
        resp = await client.post(
            "/items", data=to_json(new_item).decode("utf-8"), headers=headers
        )
        assert resp.status == 201
        data = await resp.json()
        assert data["id"] == 3
        assert data["name"] == "New Item"
        assert data["description"] == "New Description"

    @pytest.mark.asyncio
    async def test_create_item_incorrect(self, client):
        """Test creating an item with invalid data"""
        new_item = {"name": None, "description": "New Description"}
        headers = {"Content-Type": "application/json"}
        resp = await client.post(
            "/items", data=to_json(new_item).decode("utf-8"), headers=headers
        )
        assert resp.status == 422
        data = await resp.json()
        assert "Validation error for parameter" in data["error"]["message"]

    @pytest.mark.asyncio
    async def test_create_item_invalid_json(self, client):
        """Test creating an item with invalid JSON"""
        headers = {"Content-Type": "application/json"}
        resp = await client.post("/items", data="incorrect json", headers=headers)
        assert resp.status == 422
        data = await resp.json()
        assert "Validation error for parameter" in data["error"]["message"]

    @pytest.mark.asyncio
    async def test_update_item(self, client):
        """Test updating an item"""
        update_data = {"name": "Updated Item", "description": "Updated Description"}
        headers = {"Content-Type": "application/json"}
        resp = await client.put(
            "/items/2", data=to_json(update_data).decode("utf-8"), headers=headers
        )
        assert resp.status == 200
        data = await resp.json()
        assert data["id"] == 2
        assert data["name"] == "Updated Item"
        assert data["description"] == "Updated Description"

    @pytest.mark.asyncio
    async def test_delete_item(self, client):
        """Test deleting an item"""
        resp = await client.delete("/items/1")
        assert resp.status == 204

        # Check that the item was actually deleted
        resp = await client.get("/items/1")
        assert resp.status == 404

    @pytest.mark.asyncio
    async def test_openapi_schema_endpoint(self, client):
        """Test OpenAPI schema endpoint"""
        resp = await client.get("/openapi.json")
        assert resp.status == 200
        schema = await resp.json()
        assert schema["info"]["title"] == "Test API"
        assert "/items" in schema["paths"]
        assert "/items/{item_id}" in schema["paths"]

    @pytest.mark.asyncio
    async def test_swagger_ui_endpoint(self, client):
        """Test Swagger UI endpoint"""
        resp = await client.get("/docs")
        assert resp.status == 200
        text = await resp.text()
        assert "text/html" in resp.headers["Content-Type"]
        assert "swagger-ui" in text

    @pytest.mark.asyncio
    async def test_redoc_ui_endpoint(self, client):
        """Test ReDoc UI endpoint"""
        resp = await client.get("/redoc")
        assert resp.status == 200
        text = await resp.text()
        assert "text/html" in resp.headers["Content-Type"]
        assert "redoc" in text

    @pytest.mark.asyncio
    async def test_query_parameters_handling(self, client):
        """Test handling of query parameters"""
        # Test with a single value parameter
        response = await client.get("/list-test?param1=single_value")
        assert response.status == 200
        data = await response.json()
        assert data["received_param1"] == "single_value"

        # Test with a parameter that has multiple values
        response = await client.get(
            "/list-test?param1=first_value&param2=value1&param2=value2"
        )
        assert response.status == 200
        data = await response.json()
        assert data["received_param1"] == "first_value"
        assert isinstance(data["received_param2"], list)
        assert data["received_param2"] == ["value1", "value2"]
