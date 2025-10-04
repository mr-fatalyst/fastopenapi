import pytest
from django.conf import settings
from django.http import Http404
from django.test import AsyncClient
from django.urls import clear_url_caches, path
from pydantic import BaseModel

from fastopenapi import Cookie, DjangoAsyncRouter, Form, Header, Path, Query


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
def items_db():
    return [
        {"id": 1, "name": "Item 1", "description": "Description 1"},
        {"id": 2, "name": "Item 2", "description": "Description 2"},
    ]


@pytest.fixture
def urls(items_db):  # noqa: C901
    router = DjangoAsyncRouter(
        app=True,
        title="Test API",
        description="Test API for DjangoRouter",
        version="0.1.0",
    )

    @router.get("/list-test")
    async def list_endpoint(param1: str, param2: list[str] = None):
        """Test endpoint that returns the parameters it receives"""
        return {"received_param1": param1, "received_param2": param2}

    @router.get("/items", response_model=list[ItemResponse], tags=["items"])
    async def get_items():
        """Get all items"""
        return [Item(**item) for item in items_db]

    @router.get("/items-sync", response_model=list[ItemResponse], tags=["items"])
    def get_items_sync():
        """Get all items"""
        return [Item(**item) for item in items_db]

    @router.get("/items-fail", response_model=list[ItemResponse], tags=["items"])
    async def get_items_fail():
        """Get all items, but raise error"""
        raise Exception("TEST ERROR")

    @router.get("/items/{item_id}", response_model=ItemResponse, tags=["items"])
    def get_item(item_id: int):
        """Get an item by ID"""
        for item in items_db:
            if item["id"] == item_id:
                return Item(**item)
        raise Http404(f"Item with id {item_id} not found")

    @router.post("/items", response_model=ItemResponse, status_code=201, tags=["items"])
    async def create_item(item: CreateItemRequest):
        """Create a new item"""
        new_id = max(item["id"] for item in items_db) + 1
        new_item = {"id": new_id, "name": item.name, "description": item.description}
        items_db.append(new_item)
        return Item(**new_item)

    @router.put("/items/{item_id}", response_model=ItemResponse, tags=["items"])
    async def update_item(item_id: int, item: CreateItemRequest):
        """Update an item"""
        for existing_item in items_db:
            if existing_item["id"] == item_id:
                existing_item["name"] = item.name
                existing_item["description"] = item.description
                return Item(**existing_item)
        raise Http404(f"Item with id {item_id} not found")

    @router.delete("/items/{item_id}", status_code=204, tags=["items"])
    async def delete_item(item_id: int):
        """Delete an item"""
        for i, item in enumerate(items_db):
            if item["id"] == item_id:
                del items_db[i]
                return None
        raise Http404(f"Item with id {item_id} not found")

    @router.get("/test-headers")
    async def test_headers(
        user_agent: str = Header(None, alias="User-Agent"),
        custom_header: str = Header(None, alias="X-Custom-Header"),
        authorization: str = Header(None),
    ):
        """Test endpoint for headers"""
        return {
            "user_agent": user_agent,
            "custom_header": custom_header,
            "authorization": authorization,
        }

    @router.get("/test-echo-headers")
    async def test_echo_headers(x_request_id: str = Header(None, alias="X-Request-ID")):
        """Test endpoint that returns headers"""
        return (
            {"received": x_request_id or "none"},
            200,
            {"X-Echo-ID": x_request_id or "none", "X-Custom": "test"},
        )

    @router.get("/test-cookies")
    async def test_cookies(
        session_id: str = Cookie(None, alias="sessionid"),
        csrf_token: str = Cookie(None, alias="csrftoken"),
    ):
        """Test endpoint for cookies"""
        return {
            "session_id": session_id,
            "csrf_token": csrf_token,
        }

    @router.get("/test-query-validation")
    async def test_query_validation(
        page: int = Query(1, ge=1, le=100, description="Page number"),
        limit: int = Query(10, ge=1, le=100),
        search: str = Query(None, min_length=3, max_length=50),
    ):
        """Test endpoint for query parameter validation"""
        return {
            "page": page,
            "limit": limit,
            "search": search,
        }

    @router.get("/test-path/{user_id}/items/{item_id}")
    async def test_multiple_path_params(
        user_id: int = Path(..., ge=1),
        item_id: int = Path(..., ge=1),
    ):
        """Test endpoint for multiple path parameters"""
        return {
            "user_id": user_id,
            "item_id": item_id,
        }

    @router.post("/test-form")
    async def test_form_data(
        username: str = Form(..., min_length=3),
        email: str = Form(...),
        age: int = Form(None, ge=0, le=120),
    ):
        """Test endpoint for form data"""
        return {
            "username": username,
            "email": email,
            "age": age,
        }

    @router.get("/test-mixed-params/{item_id}")
    async def test_mixed_params(
        item_id: int = Path(...),
        search: str = Query(None),
        user_agent: str = Header(None, alias="User-Agent"),
        session: str = Cookie(None),
    ):
        """Test endpoint with mixed parameter types"""
        return {
            "item_id": item_id,
            "search": search,
            "user_agent": user_agent,
            "session": session,
        }

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
        return png_data, 200, {"Content-Type": "image/png"}

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
        return "Hello, World!", 200, {"Content-Type": "text/plain"}

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
        return pdf_data, 200, {"Content-Type": "application/pdf"}

    @router.get("/test-json-none")
    async def test_json_none():
        return None

    return router.urls


@pytest.fixture
def django_settings(urls):
    globals()["urlpatterns"] = [path("", urls)]
    if not settings.configured:
        settings.configure(ROOT_URLCONF=__name__)
    try:
        yield settings
    finally:
        clear_url_caches()


@pytest.fixture
def client(django_settings):
    return AsyncClient()
