import pytest


class TestDjangoIntegration:
    def test_get_items(self, client):
        """Test fetching all items"""
        response = client.get("/items")

        assert response.status_code == 200
        result = response.json()
        assert len(result) == 2
        assert result[0]["name"] == "Item 1"
        assert result[1]["name"] == "Item 2"

    def test_get_items_async(self, client):
        """Test fetching an item by ID"""
        with pytest.raises(Exception) as excinfo:
            client.get("/items-async")
            err_msg = (
                "Async endpoint 'get_items_async' cannot be used with sync router."
                " Use DjangoAsyncRouter for async support."
            )
            assert err_msg in str(excinfo.value)

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
        assert result["error"]["message"] == ("Error parsing parameter 'item_id'")

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

    def test_headers_extraction(self, client):
        """Test header parameters extraction"""
        response = client.get(
            "/test-headers",
            HTTP_USER_AGENT="TestBot/1.0",
            HTTP_X_CUSTOM_HEADER="CustomValue",
            HTTP_AUTHORIZATION="Bearer token123",
        )

        assert response.status_code == 200
        result = response.json()
        assert result["user_agent"] == "TestBot/1.0"
        assert result["custom_header"] == "CustomValue"
        assert result["authorization"] == "Bearer token123"

    def test_echo_headers(self, client):
        """Test that headers from echo response are set"""
        response = client.get(
            "/test-echo-headers",
            HTTP_X_REQUEST_ID="test-123",
        )

        assert response.status_code == 200
        assert response["X-Echo-ID"] == "test-123"
        assert response["X-Custom"] == "test"

        result = response.json()
        assert result["received"] == "test-123"

    def test_headers_missing(self, client):
        """Test missing optional headers"""
        response = client.get("/test-headers")

        assert response.status_code == 200
        result = response.json()
        assert result["user_agent"] is None
        assert result["custom_header"] is None
        assert result["authorization"] is None

    def test_cookies_extraction(self, client):
        """Test cookie parameters extraction"""
        client.cookies["sessionid"] = "session123"
        client.cookies["csrftoken"] = "csrf456"

        response = client.get("/test-cookies")

        assert response.status_code == 200
        result = response.json()
        assert result["session_id"] == "session123"
        assert result["csrf_token"] == "csrf456"

    def test_cookies_missing(self, client):
        """Test missing optional cookies"""
        response = client.get("/test-cookies")

        assert response.status_code == 200
        result = response.json()
        assert result["session_id"] is None
        assert result["csrf_token"] is None

    def test_query_validation_valid(self, client):
        """Test query parameter validation with valid data"""
        response = client.get("/test-query-validation?page=5&limit=20&search=test")

        assert response.status_code == 200
        result = response.json()
        assert result["page"] == 5
        assert result["limit"] == 20
        assert result["search"] == "test"

    def test_query_validation_defaults(self, client):
        """Test query parameter validation with defaults"""
        response = client.get("/test-query-validation")

        assert response.status_code == 200
        result = response.json()
        assert result["page"] == 1
        assert result["limit"] == 10
        assert result["search"] is None

    def test_query_validation_out_of_range(self, client):
        """Test query parameter validation with out of range values"""
        response = client.get("/test-query-validation?page=200")

        assert response.status_code == 400
        result = response.json()
        assert "Error parsing parameter" in result["error"]["message"]

    def test_query_validation_min_length(self, client):
        """Test query parameter validation with string too short"""
        response = client.get("/test-query-validation?search=ab")

        assert response.status_code == 400
        result = response.json()
        assert "Error parsing parameter" in result["error"]["message"]

    def test_multiple_path_params(self, client):
        """Test multiple path parameters"""
        response = client.get("/test-path/5/items/10")

        assert response.status_code == 200
        result = response.json()
        assert result["user_id"] == 5
        assert result["item_id"] == 10

    def test_path_params_validation_error(self, client):
        """Test path parameter validation error"""
        response = client.get("/test-path/0/items/10")

        assert response.status_code == 400
        result = response.json()
        assert "Error parsing parameter" in result["error"]["message"]

    def test_form_data_valid(self, client):
        """Test form data submission with valid data"""
        response = client.post(
            "/test-form",
            data={
                "username": "testuser",
                "email": "test@example.com",
                "age": 25,
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert result["username"] == "testuser"
        assert result["email"] == "test@example.com"
        assert result["age"] == 25

    def test_form_data_optional(self, client):
        """Test form data with optional fields"""
        response = client.post(
            "/test-form",
            data={
                "username": "testuser",
                "email": "test@example.com",
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert result["username"] == "testuser"
        assert result["email"] == "test@example.com"
        assert result["age"] is None

    def test_form_data_validation_error(self, client):
        """Test form data validation error"""
        response = client.post(
            "/test-form",
            data={
                "username": "ab",  # Too short
                "email": "test@example.com",
            },
        )

        assert response.status_code == 400
        result = response.json()
        assert "Error parsing parameter" in result["error"]["message"]

    def test_form_data_missing_required(self, client):
        """Test form data with missing required field"""
        response = client.post(
            "/test-form",
            data={
                "username": "testuser",
                # email is missing
            },
        )

        assert response.status_code == 400
        result = response.json()
        assert "Missing required parameter" in result["error"]["message"]

    def test_mixed_params_all_present(self, client):
        """Test endpoint with all parameter types present"""
        client.cookies["session"] = "session_value"

        response = client.get(
            "/test-mixed-params/42?search=query",
            HTTP_USER_AGENT="TestBot/1.0",
        )

        assert response.status_code == 200
        result = response.json()
        assert result["item_id"] == 42
        assert result["search"] == "query"
        assert result["user_agent"] == "TestBot/1.0"
        assert result["session"] == "session_value"

    def test_mixed_params_optional_missing(self, client):
        """Test endpoint with optional parameters missing"""
        response = client.get("/test-mixed-params/42")

        assert response.status_code == 200
        result = response.json()
        assert result["item_id"] == 42
        assert result["search"] is None
        assert result["user_agent"] is None
        assert result["session"] is None

    def test_binary_response(self, client):
        """Test binary content response"""
        response = client.get("/test-binary")
        assert response.status_code == 200
        assert response["Content-Type"] == "application/octet-stream"
        assert isinstance(response.content, bytes)
        assert response.content == b"\x00\x01\x02\x03\x04"

    def test_image_response(self, client):
        """Test image binary response"""
        response = client.get("/test-image")
        assert response.status_code == 200
        assert response["Content-Type"] == "image/png"
        assert isinstance(response.content, bytes)

    def test_csv_response(self, client):
        """Test CSV text response"""
        response = client.get("/test-csv")
        assert response.status_code == 200
        assert "text/csv" in response["Content-Type"]
        text = response.content.decode("utf-8")
        assert "name,age,city" in text
        assert "John,30,NYC" in text

    def test_xml_response(self, client):
        """Test XML text response"""
        response = client.get("/test-xml")
        assert response.status_code == 200
        assert "application/xml" in response["Content-Type"]
        text = response.content.decode("utf-8")
        assert "<root>" in text
        assert "<item>value</item>" in text

    def test_plain_text_response(self, client):
        """Test plain text response"""
        response = client.get("/test-text")
        assert response.status_code == 200
        assert "text/plain" in response["Content-Type"]
        text = response.content.decode("utf-8")
        assert text == "Hello, World!"

    def test_html_response(self, client):
        """Test HTML text response"""
        response = client.get("/test-html")
        assert response.status_code == 200
        assert "text/html" in response["Content-Type"]
        text = response.content.decode("utf-8")
        assert "<html>" in text
        assert "<body>" in text

    def test_custom_headers_in_response(self, client):
        """Test custom headers are preserved"""
        response = client.get("/test-custom-headers")
        assert response.status_code == 200
        assert response["X-Custom-Header"] == "CustomValue"
        assert response["X-Request-ID"] == "12345"

    def test_pdf_response(self, client):
        """Test PDF binary response"""
        response = client.get("/test-pdf")
        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"
        assert isinstance(response.content, bytes)
        assert response.content.startswith(b"%PDF")

    def test_json_none_response(self, client):
        """Test JSON None response"""
        response = client.get("/test-json-none")
        assert response.status_code == 200
        result = response.json()
        assert result is None
