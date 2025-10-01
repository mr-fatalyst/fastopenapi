import pytest
from django.conf import settings
from django.http import Http404
from django.test import Client
from django.urls import clear_url_caches, path
from pydantic import BaseModel

from fastopenapi import Cookie, DjangoRouter, Form, Header, Path, Query


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
    router = DjangoRouter(
        app=True,
        title="Test API",
        description="Test API for DjangoRouter",
        version="0.1.0",
    )

    @router.get("/list-test")
    def list_endpoint(param1: str, param2: list[str] = None):
        """Test endpoint that returns the parameters it receives"""
        return {"received_param1": param1, "received_param2": param2}

    @router.get("/items", response_model=list[ItemResponse], tags=["items"])
    def get_items():
        """Get all items"""
        return [Item(**item) for item in items_db]

    @router.get("/items-async", response_model=list[ItemResponse], tags=["items"])
    async def get_items_async():
        """Get all items"""
        return [Item(**item) for item in items_db]

    @router.get("/items-fail", response_model=list[ItemResponse], tags=["items"])
    def get_items_fail():
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
    def create_item(item: CreateItemRequest):
        """Create a new item"""
        new_id = max(item["id"] for item in items_db) + 1
        new_item = {"id": new_id, "name": item.name, "description": item.description}
        items_db.append(new_item)
        return Item(**new_item)

    @router.put("/items/{item_id}", response_model=ItemResponse, tags=["items"])
    def update_item(item_id: int, item: CreateItemRequest):
        """Update an item"""
        for existing_item in items_db:
            if existing_item["id"] == item_id:
                existing_item["name"] = item.name
                existing_item["description"] = item.description
                return Item(**existing_item)
        raise Http404(f"Item with id {item_id} not found")

    @router.delete("/items/{item_id}", status_code=204, tags=["items"])
    def delete_item(item_id: int):
        """Delete an item"""
        for i, item in enumerate(items_db):
            if item["id"] == item_id:
                del items_db[i]
                return None
        raise Http404(f"Item with id {item_id} not found")

    @router.get("/test-echo-headers")
    def test_echo_headers(x_request_id: str = Header(None, alias="X-Request-ID")):
        """Test endpoint that returns headers"""
        return (
            {"received": x_request_id or "none"},
            200,
            {"X-Echo-ID": x_request_id or "none", "X-Custom": "test"},
        )

    @router.get("/test-headers")
    def test_headers(
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

    @router.get("/test-cookies")
    def test_cookies(
        session_id: str = Cookie(None, alias="sessionid"),
        csrf_token: str = Cookie(None, alias="csrftoken"),
    ):
        """Test endpoint for cookies"""
        return {
            "session_id": session_id,
            "csrf_token": csrf_token,
        }

    @router.get("/test-query-validation")
    def test_query_validation(
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
    def test_multiple_path_params(
        user_id: int = Path(..., ge=1),
        item_id: int = Path(..., ge=1),
    ):
        """Test endpoint for multiple path parameters"""
        return {
            "user_id": user_id,
            "item_id": item_id,
        }

    @router.post("/test-form")
    def test_form_data(
        username: str = Form(..., min_length=3),
        email: str = Form(...),
        age: int | None = Form(default=None, ge=0, le=120),
    ):
        """Test endpoint for form data"""
        return {
            "username": username,
            "email": email,
            "age": age,
        }

    @router.get("/test-mixed-params/{item_id}")
    def test_mixed_params(
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
    return Client()
