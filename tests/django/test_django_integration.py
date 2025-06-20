class TestDjangoIntegration:
    def test_get_items(self, client):
        """Test fetching all items"""
        response = client.get("/items")

        assert response.status_code == 200
        result = response.json()
        assert len(result) == 2
        assert result[0]["name"] == "Item 1"
        assert result[1]["name"] == "Item 2"

    def test_get_items_fail(self, client):
        """Test fetching all items with an error"""
        response = client.get("/items-fail")

        assert response.status_code == 500
        result = response.json()
        assert result["error"]["message"] == "TEST ERROR"

    def test_get_item(self, client):
        """Test fetching an item by ID"""
        response = client.get("/items/1")

        assert response.status_code == 200
        result = response.json()
        assert result["id"] == 1
        assert result["name"] == "Item 1"
        assert result["description"] == "Description 1"

    def test_get_item_bad_request(self, client):
        """Test fetching an item with an incorrect ID type"""
        response = client.get("/items/abc")

        assert response.status_code == 400
        result = response.json()
        assert result["error"]["message"] == (
            "Error parsing parameter 'item_id'. Must be a valid int"
        )

    def test_get_nonexistent_item(self, client):
        """Test fetching a nonexistent item"""
        response = client.get("/items/999")

        assert response.status_code == 404

    def test_create_item(self, client):
        """Test creating an item"""
        new_item = {"name": "New Item", "description": "New Description"}
        response = client.post("/items", new_item, content_type="application/json")

        assert response.status_code == 201
        result = response.json()
        assert result["id"] == 3
        assert result["name"] == "New Item"
        assert result["description"] == "New Description"

    def test_create_item_incorrect(self, client):
        """Test creating an item with an incorrect body"""
        new_item = {"name": None, "description": "New Description"}
        response = client.post("/items", new_item, content_type="application/json")

        assert response.status_code == 422
        result = response.json()
        assert "Validation error for parameter" in result["error"]["message"]

    def test_create_item_invalid_json(self, client):
        """Test creating an item with invalid JSON"""
        response = client.post(
            "/items", "incorrect json", content_type="application/json"
        )

        assert response.status_code == 422
        result = response.json()
        assert "Validation error for parameter" in result["error"]["message"]

    def test_update_item(self, client):
        """Test updating an item"""
        update_data = {"name": "Updated Item", "description": "Updated Description"}
        response = client.put("/items/2", update_data, content_type="application/json")

        assert response.status_code == 200
        result = response.json()
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
        schema = response.json()
        assert schema["info"]["title"] == "Test API"
        assert "/items" in schema["paths"]
        assert "/items/{item_id}" in schema["paths"]

    def test_swagger_ui_endpoint(self, client):
        """Test Swagger UI endpoint"""
        response = client.get("/docs")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "swagger-ui" in response.content.decode("utf-8")

    def test_redoc_ui_endpoint(self, client):
        """Test ReDoc UI endpoint"""
        response = client.get("/redoc")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "redoc" in response.content.decode("utf-8")

    def test_query_parameters_handling(self, client):
        """Test handling of query parameters"""
        # Test with a single value parameter
        response = client.get("/list-test?param1=single_value")
        assert response.status_code == 200
        data = response.json()
        assert data["received_param1"] == "single_value"

        # Test with a parameter that has multiple values
        response = client.get(
            "/list-test?param1=first_value&param2=value1&param2=value2"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["received_param1"] == "first_value"
        assert isinstance(data["received_param2"], list)
        assert data["received_param2"] == ["value1", "value2"]
