from pydantic import BaseModel
from pydantic_core import from_json, to_json
from tornado.testing import AsyncHTTPTestCase, gen_test
from tornado.web import Application, HTTPError

from fastopenapi import Header
from fastopenapi.routers import TornadoRouter


# Pydantic models
class Item(BaseModel):
    id: int
    name: str
    description: str = None


class CreateItemRequest(BaseModel):
    name: str
    description: str = None


class ItemResponse(BaseModel):
    id: int
    name: str
    description: str = None


class TestTornadoIntegration(AsyncHTTPTestCase):
    def get_app(self):  # noqa: C901

        self.items_db = [
            {"id": 1, "name": "Item 1", "description": "Description 1"},
            {"id": 2, "name": "Item 2", "description": "Description 2"},
        ]

        app = Application()

        router = TornadoRouter(
            app=app,
            title="Test API",
            description="Test API for TornadoRouter",
            version="0.1.0",
        )

        @router.get("/list-test")
        async def list_endpoint(param1: str, param2: list[str] = None):
            """Test endpoint that returns the parameters it receives"""
            return {"received_param1": param1, "received_param2": param2}

        @router.head("/health")
        def health_head():
            """HEAD request for health check - returns only headers"""
            return (
                None,
                200,
                {"X-Status": "Ok"},
            )

        @router.options("/items")
        def service_options():
            """OPTIONS request showing available methods"""
            return (
                None,
                204,
                {"Allow": "GET, POST, HEAD, OPTIONS", "X-RateLimit": "100 per hour"},
            )

        @router.get("/test-echo-headers")
        def echo_headers(x_request_id: str = Header(None, alias="X-Request-ID")):
            """Test endpoint that returns headers"""
            return (
                {"received": x_request_id or "none"},
                200,
                {"X-Echo-ID": x_request_id or "none", "X-Custom": "test"},
            )

        @router.get("/items-sync", response_model=list[ItemResponse], tags=["items"])
        def get_items_sync():
            return [ItemResponse(**item) for item in self.items_db]

        @router.get("/items", response_model=list[ItemResponse], tags=["items"])
        async def get_items():
            return [ItemResponse(**item) for item in self.items_db]

        @router.get("/items-invalid", response_model=list[ItemResponse], tags=["items"])
        async def get_items_invalid():
            return [Item(**item) for item in self.items_db]

        @router.get("/items-fail", response_model=list[ItemResponse], tags=["items"])
        async def get_items_fail():
            raise Exception("TEST ERROR")

        @router.get("/items/{item_id}", response_model=ItemResponse, tags=["items"])
        async def get_item(item_id: int):
            for item in self.items_db:
                if item["id"] == item_id:
                    return ItemResponse(**item)
            raise HTTPError(status_code=404, log_message="Not Found")

        @router.post(
            "/items", response_model=ItemResponse, status_code=201, tags=["items"]
        )
        async def create_item(item: CreateItemRequest):
            new_id = max(existing_item["id"] for existing_item in self.items_db) + 1
            new_item = {
                "id": new_id,
                "name": item.name,
                "description": item.description,
            }
            self.items_db.append(new_item)
            return ItemResponse(**new_item)

        @router.patch("/items/{item_id}", response_model=ItemResponse, tags=["items"])
        async def update_item(item_id: int, item: CreateItemRequest):
            for existing_item in self.items_db:
                if existing_item["id"] == item_id:
                    if item.name:
                        existing_item["name"] = item.name
                    if item.description:
                        existing_item["description"] = item.description
                    return ItemResponse(**existing_item)
            raise HTTPError(status_code=404, log_message="Not Found")

        @router.put("/items/{item_id}", response_model=ItemResponse, tags=["items"])
        async def insert_item(item_id: int, item: CreateItemRequest):
            for existing_item in self.items_db:
                if existing_item["id"] == item_id:
                    existing_item["name"] = item.name
                    existing_item["description"] = item.description
                    return ItemResponse(**existing_item)
            raise HTTPError(status_code=404, log_message="Not Found")

        @router.delete("/items/{item_id}", status_code=204, tags=["items"])
        async def delete_item(item_id: int):
            for i, item in enumerate(self.items_db):
                if item["id"] == item_id:
                    del self.items_db[i]
                    return None
            raise HTTPError(status_code=404, log_message="Not Found")

        @router.get("/test-binary")
        async def test_binary():
            return (
                b"\x00\x01\x02\x03\x04",
                200,
                {"Content-Type": "application/octet-stream"},
            )

        @router.get("/test-image")
        async def test_image():
            png_data = (
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00"
                b"\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx"
                b"\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00"
                b"IEND\xaeB`\x82"
            )
            return (png_data, 200, {"Content-Type": "image/png"})

        @router.get("/test-csv")
        async def test_csv():
            return (
                "name,age,city\nJohn,30,NYC\nJane,25,LA",
                200,
                {"Content-Type": "text/csv"},
            )

        @router.get("/test-xml")
        async def test_xml():
            return (
                "<?xml version='1.0'?><root><item>value</item></root>",
                200,
                {"Content-Type": "application/xml"},
            )

        @router.get("/test-text")
        async def test_text():
            return ("Hello, World!", 200, {"Content-Type": "text/plain"})

        @router.get("/test-html")
        async def test_html():
            return (
                "<html><body><h1>Test</h1></body></html>",
                200,
                {"Content-Type": "text/html"},
            )

        @router.get("/test-custom-headers")
        async def test_custom_headers():
            return (
                {"message": "test"},
                200,
                {"X-Custom-Header": "CustomValue", "X-Request-ID": "12345"},
            )

        @router.get("/test-pdf")
        async def test_pdf():
            pdf_data = (
                b"%PDF-1.0\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<<"
                b"/Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox["
                b"0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\nxref\n0 4\n000000000"
                b"0 65535 f\n0000000009 00000 n\n0000000052 00000 n\n0000000101 00000 n"
                b"\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF"
            )
            return (pdf_data, 200, {"Content-Type": "application/pdf"})

        @router.delete("/test-no-content", status_code=204)
        async def test_no_content():
            return None

        return app

    def parse_json(self, response):
        return from_json(response.body.decode()) if response.body else {}

    @gen_test
    async def test_echo_headers(self):
        """Test that headers from echo response are set"""
        response = await self.http_client.fetch(
            self.get_url("/test-echo-headers"),
            headers={"X-Request-Id": "test-123"},
        )

        self.assertEqual(response.code, 200)
        result = self.parse_json(response)
        headers = dict(response.headers)
        self.assertEqual(headers["X-Echo-Id"], "test-123")
        self.assertEqual(headers["X-Custom"], "test")
        self.assertEqual(result["received"], "test-123")

    @gen_test
    async def test_head(self):
        """Test that headers from head response are set"""
        response = await self.http_client.fetch(
            self.get_url("/health"),
            method="HEAD",
        )

        self.assertEqual(response.code, 200)
        result = self.parse_json(response)
        headers = dict(response.headers)
        self.assertEqual(headers["X-Status"], "Ok")
        self.assertFalse(result)

    @gen_test
    async def test_options(self):
        """Test that options works"""
        response = await self.http_client.fetch(
            self.get_url("/items"),
            method="OPTIONS",
        )

        self.assertEqual(response.code, 204)
        result = self.parse_json(response)
        headers = dict(response.headers)
        self.assertEqual(headers["Allow"], "GET, POST, HEAD, OPTIONS")
        self.assertEqual(headers["X-Ratelimit"], "100 per hour")
        self.assertFalse(result)

    @gen_test
    async def test_get_items(self):
        response = await self.http_client.fetch(self.get_url("/items"))
        self.assertEqual(response.code, 200)
        result = self.parse_json(response)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "Item 1")
        self.assertEqual(result[1]["name"], "Item 2")

    @gen_test
    async def test_get_items_invalid(self):
        response = await self.http_client.fetch(
            self.get_url("/items-invalid"), raise_error=False
        )
        self.assertEqual(response.code, 500)
        result = self.parse_json(response)
        self.assertEqual(result["error"]["message"], "Incorrect response type")

    @gen_test
    async def test_get_items_sync(self):
        response = await self.http_client.fetch(self.get_url("/items-sync"))
        self.assertEqual(response.code, 200)
        result = self.parse_json(response)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "Item 1")
        self.assertEqual(result[1]["name"], "Item 2")

    @gen_test
    async def test_get_wrong_method_items(self):
        response = await self.http_client.fetch(
            self.get_url("/items"), method="DELETE", raise_error=False
        )
        self.assertEqual(response.code, 405)

    @gen_test
    async def test_get_items_fail(self):
        response = await self.http_client.fetch(
            self.get_url("/items-fail"), raise_error=False
        )
        self.assertEqual(response.code, 500)
        result = self.parse_json(response)
        self.assertIn("TEST ERROR", result["error"]["message"])

    @gen_test
    async def test_get_item(self):
        response = await self.http_client.fetch(self.get_url("/items/1"))
        self.assertEqual(response.code, 200)
        result = self.parse_json(response)
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["name"], "Item 1")
        self.assertEqual(result["description"], "Description 1")

    @gen_test
    async def test_get_item_unprocessable(self):
        response = await self.http_client.fetch(
            self.get_url("/items/abc"), raise_error=False
        )
        self.assertEqual(response.code, 422)
        result = self.parse_json(response)
        self.assertIn("Error parsing parameter", result["error"]["message"])

    @gen_test
    async def test_get_nonexistent_item(self):
        response = await self.http_client.fetch(
            self.get_url("/items/999"), raise_error=False
        )
        self.assertEqual(response.code, 404)

    @gen_test
    async def test_create_item(self):
        new_item = {"name": "New Item", "description": "New Description"}
        body = to_json(new_item).decode("utf-8")
        headers = {"Content-Type": "application/json"}
        response = await self.http_client.fetch(
            self.get_url("/items"),
            method="POST",
            headers=headers,
            body=body,
        )
        self.assertEqual(response.code, 201)
        result = self.parse_json(response)
        self.assertEqual(result["id"], 3)
        self.assertEqual(result["name"], "New Item")
        self.assertEqual(result["description"], "New Description")

    @gen_test
    async def test_create_item_incorrect(self):
        new_item = {"name": None, "description": "New Description"}
        body = to_json(new_item).decode("utf-8")
        headers = {"Content-Type": "application/json"}
        response = await self.http_client.fetch(
            self.get_url("/items"),
            method="POST",
            headers=headers,
            body=body,
            raise_error=False,
        )
        self.assertEqual(response.code, 422)
        result = self.parse_json(response)
        self.assertIn("Validation error", result["error"]["message"])

    @gen_test
    async def test_create_item_invalid_json(self):
        body = b"incorrect json"
        headers = {"Content-Type": "application/json"}
        response = await self.http_client.fetch(
            self.get_url("/items"),
            method="POST",
            headers=headers,
            body=body,
            raise_error=False,
        )
        self.assertEqual(response.code, 422)
        result = self.parse_json(response)
        detail = result["error"]["message"]
        self.assertTrue("Validation error" in detail or "JSON" in detail)

    @gen_test
    async def test_update_item(self):
        update_data = {"name": "Updated Item"}
        body = to_json(update_data).decode("utf-8")
        headers = {"Content-Type": "application/json"}
        response = await self.http_client.fetch(
            self.get_url("/items/2"),
            method="PATCH",
            headers=headers,
            body=body,
        )
        self.assertEqual(response.code, 200)
        result = self.parse_json(response)
        self.assertEqual(result["id"], 2)
        self.assertEqual(result["name"], "Updated Item")
        self.assertEqual(result["description"], "Description 2")

    @gen_test
    async def test_update_full_item(self):
        update_data = {"name": "Updated Item", "description": "Updated Description"}
        body = to_json(update_data).decode("utf-8")
        headers = {"Content-Type": "application/json"}
        response = await self.http_client.fetch(
            self.get_url("/items/2"),
            method="PUT",
            headers=headers,
            body=body,
        )
        self.assertEqual(response.code, 200)
        result = self.parse_json(response)
        self.assertEqual(result["id"], 2)
        self.assertEqual(result["name"], "Updated Item")
        self.assertEqual(result["description"], "Updated Description")

    @gen_test
    async def test_delete_item(self):
        response = await self.http_client.fetch(
            self.get_url("/items/1"), method="DELETE", raise_error=False
        )
        self.assertEqual(response.code, 204)
        # Verify deletion
        response = await self.http_client.fetch(
            self.get_url("/items/1"), raise_error=False
        )
        self.assertEqual(response.code, 404)

    @gen_test
    async def test_openapi_schema_endpoint(self):
        response = await self.http_client.fetch(self.get_url("/openapi.json"))
        self.assertEqual(response.code, 200)
        schema = self.parse_json(response)
        self.assertEqual(schema["info"]["title"], "Test API")
        self.assertIn("/items", schema["paths"])
        self.assertIn("/items/{item_id}", schema["paths"])

    @gen_test
    async def test_swagger_ui_endpoint(self):
        response = await self.http_client.fetch(self.get_url("/docs"))
        self.assertEqual(response.code, 200)
        self.assertIn("text/html", response.headers.get("Content-Type", ""))
        html_text = response.body.decode().lower()
        self.assertIn("swagger-ui", html_text)

    @gen_test
    async def test_redoc_ui_endpoint(self):
        response = await self.http_client.fetch(self.get_url("/redoc"))
        self.assertEqual(response.code, 200)
        self.assertIn("text/html", response.headers.get("Content-Type", ""))
        html_text = response.body.decode().lower()
        self.assertIn("redoc", html_text)

    @gen_test
    async def test_query_parameters_handling(self):
        """Test handling of query parameters"""
        # Test with a single value parameter
        response = await self.http_client.fetch(
            self.get_url("/list-test?param1=single_value"), raise_error=False
        )
        self.assertEqual(response.code, 200)
        data = self.parse_json(response)
        self.assertEqual(data["received_param1"], "single_value")

        # Test with a parameter that has multiple values
        response = await self.http_client.fetch(
            self.get_url("/list-test?param1=first_value&param2=value1&param2=value2"),
            raise_error=False,
        )
        self.assertEqual(response.code, 200)
        data = self.parse_json(response)
        self.assertEqual(data["received_param1"], "first_value")
        self.assertTrue(isinstance(data["received_param2"], list))
        self.assertEqual(data["received_param2"], ["value1", "value2"])

    @gen_test
    async def test_binary_response(self):
        """Test binary content response"""
        response = await self.http_client.fetch(self.get_url("/test-binary"))
        self.assertEqual(response.code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/octet-stream")
        self.assertIsInstance(response.body, bytes)
        self.assertEqual(response.body, b"\x00\x01\x02\x03\x04")

    @gen_test
    async def test_image_response(self):
        """Test image binary response"""
        response = await self.http_client.fetch(self.get_url("/test-image"))
        self.assertEqual(response.code, 200)
        self.assertEqual(response.headers["Content-Type"], "image/png")
        self.assertIsInstance(response.body, bytes)

    @gen_test
    async def test_csv_response(self):
        """Test CSV text response"""
        response = await self.http_client.fetch(self.get_url("/test-csv"))
        self.assertEqual(response.code, 200)
        self.assertIn("text/csv", response.headers["Content-Type"])
        text = response.body.decode("utf-8")
        self.assertIn("name,age,city", text)
        self.assertIn("John,30,NYC", text)

    @gen_test
    async def test_xml_response(self):
        """Test XML text response"""
        response = await self.http_client.fetch(self.get_url("/test-xml"))
        self.assertEqual(response.code, 200)
        self.assertIn("application/xml", response.headers["Content-Type"])
        text = response.body.decode("utf-8")
        self.assertIn("<root>", text)
        self.assertIn("<item>value</item>", text)

    @gen_test
    async def test_plain_text_response(self):
        """Test plain text response"""
        response = await self.http_client.fetch(self.get_url("/test-text"))
        self.assertEqual(response.code, 200)
        self.assertIn("text/plain", response.headers["Content-Type"])
        text = response.body.decode("utf-8")
        self.assertEqual(text, "Hello, World!")

    @gen_test
    async def test_html_response(self):
        """Test HTML text response"""
        response = await self.http_client.fetch(self.get_url("/test-html"))
        self.assertEqual(response.code, 200)
        self.assertIn("text/html", response.headers["Content-Type"])
        text = response.body.decode("utf-8")
        self.assertIn("<html>", text)
        self.assertIn("<body>", text)

    @gen_test
    async def test_custom_headers_in_response(self):
        """Test custom headers are preserved"""
        response = await self.http_client.fetch(self.get_url("/test-custom-headers"))
        self.assertEqual(response.code, 200)
        self.assertEqual(response.headers["X-Custom-Header"], "CustomValue")
        self.assertEqual(response.headers["X-Request-Id"], "12345")

    @gen_test
    async def test_pdf_response(self):
        """Test PDF binary response"""
        response = await self.http_client.fetch(self.get_url("/test-pdf"))
        self.assertEqual(response.code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/pdf")
        self.assertIsInstance(response.body, bytes)
        self.assertTrue(response.body.startswith(b"%PDF"))

    @gen_test
    async def test_no_content_204(self):
        """Test 204 No Content response has no body"""
        response = await self.http_client.fetch(
            self.get_url("/test-no-content"), method="DELETE"
        )
        self.assertEqual(response.code, 204)
        self.assertEqual(len(response.body), 0)
