import pytest
from django.conf import settings
from django.http import Http404
from django.test import Client
from django.urls import path
from pydantic import BaseModel

from fastopenapi.routers import DjangoRouter


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

    @router.get("/items-sync", response_model=list[ItemResponse], tags=["items"])
    def get_items_sync():
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

    return router.urls


@pytest.fixture
def django_settings(urls):
    globals()["urlpatterns"] = [path("", urls)]
    if not settings.configured:
        settings.configure(ROOT_URLCONF=__name__)
    return settings


@pytest.fixture
def client(django_settings):
    return Client()
