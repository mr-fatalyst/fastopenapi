from aiohttp import web

from benchmarks.aiohttp.with_fastopenapi.schemas import (
    RecordCreate,
    RecordResponse,
    RecordUpdate,
)
from benchmarks.aiohttp.with_fastopenapi.storage import RecordStore
from fastopenapi.routers import AioHttpRouter

# Initialize AioHttp app and router
app = web.Application()
router = AioHttpRouter(
    app=app,
    title="Record API",
    description="A simple Record API built with FastOpenAPI and AioHttp",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Initialize the storage
store = RecordStore()


# Define routes using the AioHttpRouter decorators
@router.get("/records", tags=["records"], response_model=list[RecordResponse])
async def get_records():
    """
    Get all records
    """
    return store.get_all()


@router.get("/records/{record_id}", tags=["records"], response_model=RecordResponse)
async def get_record(record_id: str):
    """
    Get a specific record by ID
    """
    record = store.get_by_id(record_id)
    if not record:
        raise web.HTTPNotFound(reason="Not Found")
    return record


@router.post(
    "/records", tags=["records"], status_code=201, response_model=RecordResponse
)
async def create_record(record: RecordCreate):
    """
    Create a new record
    """
    return store.create(record)


@router.put("/records/{record_id}", tags=["records"], response_model=RecordResponse)
async def update_record_full(record_id: str, record: RecordCreate):
    """
    Update a record completely (all fields required)
    """
    existing_record = store.get_by_id(record_id)
    if not existing_record:
        raise web.HTTPNotFound(reason="Not Found")

    # Delete and recreate with the same ID
    store.delete(record_id)
    new_record = {"id": record_id, **record.model_dump()}
    store.records[record_id] = new_record
    return RecordResponse(**new_record)


@router.patch("/records/{record_id}", tags=["records"], response_model=RecordResponse)
async def update_record_partial(record_id: str, record: RecordUpdate):
    """
    Update a record partially (only specified fields)
    """
    updated_record = store.update(record_id, record)
    if not updated_record:
        raise web.HTTPNotFound(reason="Not Found")
    return updated_record


@router.delete("/records/{record_id}", tags=["records"], status_code=204)
async def delete_record(record_id: str):
    """
    Delete a record
    """
    if not store.delete(record_id):
        raise web.HTTPNotFound(reason="Not Found")
    return None


if __name__ == "__main__":
    web.run_app(app, host="127.0.0.1", port=8001)
