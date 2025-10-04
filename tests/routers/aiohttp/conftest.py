import pytest
from aiohttp import web
from pydantic import BaseModel

from fastopenapi.routers import AioHttpRouter


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


@pytest.fixture
async def dummy_endpoint():
    return {"message": "dummy"}


@pytest.fixture
def items_db():
    return [
        {"id": 1, "name": "Item 1", "description": "Description 1"},
        {"id": 2, "name": "Item 2", "description": "Description 2"},
    ]


@pytest.fixture
def app(items_db):  # noqa: C901
    app = web.Application()
    router = AioHttpRouter(
        app=app,
        title="Test API",
        description="Test API for AioHttpRouter",
        version="0.1.0",
    )

    @router.get("/list-test")
    def list_endpoint(param1: str, param2: list[str] = None):
        """Test endpoint that returns the parameters it receives"""
        return {"received_param1": param1, "received_param2": param2}

    @router.get("/items", response_model=list[ItemResponse], tags=["items"])
    async def get_items():
        return [Item(**item) for item in items_db]

    @router.get("/items-sync", response_model=list[ItemResponse], tags=["items"])
    def get_items_sync():
        return [Item(**item) for item in items_db]

    @router.get("/items-fail", response_model=list[ItemResponse], tags=["items"])
    async def get_items_fail():
        raise Exception("TEST ERROR")

    @router.get("/items/{item_id}", response_model=ItemResponse, tags=["items"])
    async def get_item(item_id: int):
        for item in items_db:
            if item["id"] == item_id:
                return Item(**item)
        raise web.HTTPNotFound(text="Not Found")

    @router.post("/items", response_model=ItemResponse, status_code=201, tags=["items"])
    async def create_item(item: CreateItemRequest):
        new_id = max(item_["id"] for item_ in items_db) + 1
        new_item = {"id": new_id, "name": item.name, "description": item.description}
        items_db.append(new_item)
        return Item(**new_item)

    @router.put("/items/{item_id}", response_model=ItemResponse, tags=["items"])
    async def update_item(item_id: int, item: CreateItemRequest):
        for existing_item in items_db:
            if existing_item["id"] == item_id:
                existing_item["name"] = item.name
                existing_item["description"] = item.description
                return Item(**existing_item)
        raise web.HTTPNotFound(text="Not Found")

    @router.delete("/items/{item_id}", status_code=204, tags=["items"])
    async def delete_item(item_id: int):
        for i, item in enumerate(items_db):
            if item["id"] == item_id:
                del items_db[i]
                return None
        raise web.HTTPNotFound(text="Not Found")

    @router.get("/test-binary")
    async def get_binary():
        return (
            b"\x00\x01\x02\x03\x04",
            200,
            {"Content-Type": "application/octet-stream"},
        )

    @router.get("/test-image")
    async def get_image():
        # Minimal valid 1x1 PNG
        png_data = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00"
            b"\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx"
            b"\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00"
            b"IEND\xaeB`\x82"
        )
        return png_data, 200, {"Content-Type": "image/png"}

    @router.get("/test-csv")
    async def get_csv():
        csv_content = "name,age,city\nJohn,30,NYC\nJane,25,LA"
        return csv_content, 200, {"Content-Type": "text/csv"}

    @router.get("/test-xml")
    async def get_xml():
        xml_content = "<?xml version='1.0'?><root><item>value</item></root>"
        return xml_content, 200, {"Content-Type": "application/xml"}

    @router.get("/test-text")
    async def get_text():
        return "Hello, World!", 200, {"Content-Type": "text/plain"}

    @router.get("/test-html")
    async def get_html():
        html_content = "<html><body><h1>Test</h1></body></html>"
        return html_content, 200, {"Content-Type": "text/html"}

    @router.get("/test-custom-headers")
    async def get_custom_headers():
        return (
            {"message": "test"},
            200,
            {"X-Custom-Header": "CustomValue", "X-Request-ID": "12345"},
        )

    @router.get("/test-pdf")
    async def get_pdf():
        # Minimal valid PDF
        pdf_data = (
            b"%PDF-1.0\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<<"
            b"/Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox["
            b"0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\nxref\n0 4\n000000000"
            b"0 65535 f\n0000000009 00000 n\n0000000052 00000 n\n0000000101 00000 n"
            b"\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF"
        )
        return pdf_data, 200, {"Content-Type": "application/pdf"}

    return app


@pytest.fixture
def client(app, event_loop):
    from aiohttp.test_utils import TestClient, TestServer

    server = TestServer(app, loop=event_loop)
    event_loop.run_until_complete(server.start_server())
    client = TestClient(server, loop=event_loop)
    event_loop.run_until_complete(client.start_server())
    yield client
    event_loop.run_until_complete(client.close())
    event_loop.run_until_complete(server.close())
