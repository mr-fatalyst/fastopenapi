import json

from pydantic import BaseModel
from tornado.testing import AsyncHTTPTestCase, gen_test
from tornado.web import Application, HTTPError

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

        @router.get("/items-sync", response_model=list[ItemResponse], tags=["items"])
        def get_items_sync():
            return [Item(**item) for item in self.items_db]

        @router.get("/items", response_model=list[ItemResponse], tags=["items"])
        async def get_items():
            return [Item(**item) for item in self.items_db]

        @router.get("/items-fail", response_model=list[ItemResponse], tags=["items"])
        async def get_items_fail():
            raise Exception("TEST ERROR")

        @router.get("/items/{item_id}", response_model=ItemResponse, tags=["items"])
        async def get_item(item_id: int):
            for item in self.items_db:
                if item["id"] == item_id:
                    return Item(**item)
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
            return Item(**new_item)

        @router.patch("/items/{item_id}", response_model=ItemResponse, tags=["items"])
        async def update_item(item_id: int, item: CreateItemRequest):
            for existing_item in self.items_db:
                if existing_item["id"] == item_id:
                    if item.name:
                        existing_item["name"] = item.name
                    if item.description:
                        existing_item["description"] = item.description
                    return Item(**existing_item)
            raise HTTPError(status_code=404, log_message="Not Found")

        @router.put("/items/{item_id}", response_model=ItemResponse, tags=["items"])
        async def insert_item(item_id: int, item: CreateItemRequest):
            for existing_item in self.items_db:
                if existing_item["id"] == item_id:
                    existing_item["name"] = item.name
                    existing_item["description"] = item.description
                    return Item(**existing_item)
            raise HTTPError(status_code=404, log_message="Not Found")

        @router.delete("/items/{item_id}", status_code=204, tags=["items"])
        async def delete_item(item_id: int):
            for i, item in enumerate(self.items_db):
                if item["id"] == item_id:
                    del self.items_db[i]
                    return None
            raise HTTPError(status_code=404, log_message="Not Found")

        return app

    def parse_json(self, response):
        return json.loads(response.body.decode())

    @gen_test
    async def test_get_items(self):
        response = await self.http_client.fetch(self.get_url("/items"))
        self.assertEqual(response.code, 200)
        result = self.parse_json(response)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "Item 1")
        self.assertEqual(result[1]["name"], "Item 2")

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
        self.assertEqual(response.code, 400)
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
        body = json.dumps(new_item).encode()
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
        body = json.dumps(new_item).encode()
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
        body = json.dumps(update_data).encode()
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
        body = json.dumps(update_data).encode()
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
