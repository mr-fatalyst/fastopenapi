import pytest
from pydantic_core import from_json, to_json


class TestFlaskIntegration:

    def test_get_items(self, client):
        """Test fetching all items"""
        response = client.get("/items")

        assert response.status_code == 200
        result = from_json(response.text)
        assert len(result) == 2
        assert result[0]["name"] == "Item 1"
        assert result[1]["name"] == "Item 2"

    def test_get_headers(self, client):
        """Test fetching all items"""
        response = client.get(
            "/test-echo-headers", headers={"HTTP_X_REQUEST_ID": "test-123"}
        )

        assert response.status_code == 200
        result = from_json(response.text)
        headers = dict(response.headers)
        assert headers["X-Echo-ID"] == "test-123"
        assert headers["X-Custom"] == "test"
        assert result["received"] == "test-123"

    def test_get_items_async(self, client):
        """Test fetching an item by ID"""
        with pytest.raises(Exception) as excinfo:
            client.get("/items-async")
            err_msg = (
                "Async endpoint 'get_items_async'"
                " cannot be used with Flask. Use Quart for async support."
            )
            assert err_msg in str(excinfo.value)

    def test_get_items_fail(self, client):
        """Test fetching all items with an error"""
        response = client.get("/items-fail")

        assert response.status_code == 500
        result = from_json(response.text)
        assert result["error"]["message"] == "TEST ERROR"

    def test_get_item(self, client):
        """Test fetching an item by ID"""
        response = client.get("/items/1")

        assert response.status_code == 200
        result = from_json(response.text)
        assert result["id"] == 1
        assert result["name"] == "Item 1"
        assert result["description"] == "Description 1"

    def test_get_item_bad_request(self, client):
        """Test fetching an item with an incorrect ID type"""
        response = client.get("/items/abc")

        assert response.status_code == 400
        result = from_json(response.text)
        assert result["error"]["message"] == ("Error parsing parameter 'item_id'")

    def test_get_nonexistent_item(self, client):
        """Test fetching a nonexistent item"""
        response = client.get("/items/999")

        assert response.status_code == 404

    def test_create_item(self, client):
        """Test creating an item"""
        new_item = {"name": "New Item", "description": "New Description"}
        response = client.post(
            "/items",
            data=to_json(new_item).decode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 201
        result = from_json(response.text)
        assert result["id"] == 3
        assert result["name"] == "New Item"
        assert result["description"] == "New Description"

    def test_create_item_incorrect(self, client):
        """Test creating an item with an incorrect body"""
        new_item = {"name": None, "description": "New Description"}
        response = client.post(
            "/items",
            data=to_json(new_item).decode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422
        result = from_json(response.text)
        assert "Validation error for parameter" in result["error"]["message"]

    def test_create_item_invalid_json(self, client):
        """Test creating an item with invalid JSON"""
        response = client.post(
            "/items",
            data="incorrect json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422
        result = from_json(response.text)
        assert "Validation error for parameter" in result["error"]["message"]

    def test_update_item(self, client):
        """Test updating an item"""
        update_data = {"name": "Updated Item", "description": "Updated Description"}
        response = client.put(
            "/items/2",
            data=to_json(update_data).decode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        result = from_json(response.text)
        assert result["id"] == 2
        assert result["name"] == "Updated Item"
        assert result["description"] == "Updated Description"

    def test_delete_item(self, client):
        """Test deleting an item"""
        response = client.delete("/items/1")

        assert response.status_code == 204

        # Verify that the item has actually been deleted
        response = client.get("/items/1")
        assert response.status_code == 404

    def test_openapi_schema_endpoint(self, client):
        """Test OpenAPI schema endpoint"""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        schema = from_json(response.text)
        assert schema["info"]["title"] == "Test API"
        assert "/items" in schema["paths"]
        assert "/items/{item_id}" in schema["paths"]

    def test_swagger_ui_endpoint(self, client):
        """Test Swagger UI endpoint"""
        response = client.get("/docs")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "swagger-ui" in response.text

    def test_redoc_ui_endpoint(self, client):
        """Test ReDoc UI endpoint"""
        response = client.get("/redoc")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "redoc" in response.text

    def test_query_parameters_handling(self, client):
        """Test handling of query parameters"""
        # Test with a single value parameter
        response = client.get("/list-test?param1=single_value")
        assert response.status_code == 200
        data = response.get_json()
        assert data["received_param1"] == "single_value"

        # Test with a parameter that has multiple values
        response = client.get(
            "/list-test?param1=first_value&param2=value1&param2=value2"
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["received_param1"] == "first_value"
        assert isinstance(data["received_param2"], list)
        assert data["received_param2"] == ["value1", "value2"]
