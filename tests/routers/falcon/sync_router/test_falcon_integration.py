import pytest
from pydantic_core import from_json, to_json


class TestFalconIntegration:

    def test_get_items_sync(self, sync_client):
        """Test fetching all items synchronously"""
        with pytest.raises(Exception) as excinfo:
            sync_client.simulate_get("/items-async")
            err_msg = (
                "Async endpoint 'get_items_async' cannot be used with sync router."
                " Use FalconAsyncRouter for async support."
            )
            assert err_msg in str(excinfo.value)

    def test_get_items(self, sync_client):
        """Test fetching all items"""
        response = sync_client.simulate_get("/items")

        assert response.status_code == 200
        result = from_json(response.text)
        assert len(result) == 2
        assert result[0]["name"] == "Item 1"
        assert result[1]["name"] == "Item 2"

    def test_get_items_fail(self, sync_client):
        """Test fetching all items with an error"""
        response = sync_client.simulate_get("/items-fail")

        assert response.status_code == 500
        result = from_json(response.text)
        assert result["error"]["message"] == "TEST ERROR"

    def test_get_item(self, sync_client):
        """Test fetching an item by ID"""
        response = sync_client.simulate_get("/items/1")

        assert response.status_code == 200
        result = from_json(response.text)
        assert result["id"] == 1
        assert result["name"] == "Item 1"
        assert result["description"] == "Description 1"

    def test_get_item_bad_request(self, sync_client):
        """Test fetching an item with an incorrect ID type"""
        response = sync_client.simulate_get("/items/abc")

        assert response.status_code == 400
        result = from_json(response.text)
        assert result["error"]["message"] == ("Error parsing parameter 'item_id'")

    def test_get_nonexistent_item(self, sync_client):
        """Test fetching a nonexistent item"""
        response = sync_client.simulate_get("/items/999")

        assert response.status_code == 404

    def test_create_item(self, sync_client):
        """Test creating an item"""
        new_item = {"name": "New Item", "description": "New Description"}
        response = sync_client.simulate_post(
            "/items",
            body=to_json(new_item).decode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 201
        result = from_json(response.text)
        assert result["id"] == 3
        assert result["name"] == "New Item"
        assert result["description"] == "New Description"

    def test_create_item_incorrect(self, sync_client):
        """Test creating an item with an incorrect body"""
        new_item = {"name": None, "description": "New Description"}
        response = sync_client.simulate_post(
            "/items",
            body=to_json(new_item).decode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422
        result = from_json(response.text)
        assert "Validation error for parameter" in result["error"]["message"]

    def test_create_item_invalid_json(self, sync_client):
        """Test creating an item with invalid JSON"""
        response = sync_client.simulate_post(
            "/items",
            body="incorrect json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422
        result = from_json(response.text)
        assert "Validation error for parameter" in result["error"]["message"]

    def test_update_item(self, sync_client):
        """Test updating an item"""
        update_data = {"name": "Updated Item", "description": "Updated Description"}
        response = sync_client.simulate_put(
            "/items/2",
            body=to_json(update_data).decode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        result = from_json(response.text)
        assert result["id"] == 2
        assert result["name"] == "Updated Item"
        assert result["description"] == "Updated Description"

    def test_delete_item(self, sync_client):
        """Test deleting an item"""
        response = sync_client.simulate_delete("/items/1")

        assert response.status_code == 204

        # Verify that the item has actually been deleted
        response = sync_client.simulate_get("/items/1")
        assert response.status_code == 404

    def test_openapi_schema_endpoint(self, sync_client):
        """Test OpenAPI schema endpoint"""
        response = sync_client.simulate_get("/openapi.json")

        assert response.status_code == 200
        schema = from_json(response.text)
        assert schema["info"]["title"] == "Test API"
        assert "/items" in schema["paths"]
        assert "/items/{item_id}" in schema["paths"]

    def test_swagger_ui_endpoint(self, sync_client):
        """Test Swagger UI endpoint"""
        response = sync_client.simulate_get("/docs")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "swagger-ui" in response.text

    def test_redoc_ui_endpoint(self, sync_client):
        """Test ReDoc UI endpoint"""
        response = sync_client.simulate_get("/redoc")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "redoc" in response.text

    def test_query_parameters_handling(self, sync_client):
        """Test handling of query parameters"""
        # Test with a single value parameter
        response = sync_client.get("/list-test?param1=single_value")
        assert response.status_code == 200
        data = from_json(response.text)
        assert data["received_param1"] == "single_value"

        # Test with a parameter that has multiple values
        response = sync_client.get(
            "/list-test?param1=first_value&param2=value1&param2=value2"
        )
        assert response.status_code == 200
        data = from_json(response.text)
        assert data["received_param1"] == "first_value"
        assert isinstance(data["received_param2"], list)
        assert data["received_param2"] == ["value1", "value2"]
