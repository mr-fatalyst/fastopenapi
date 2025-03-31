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
