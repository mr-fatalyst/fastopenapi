import asyncio

from tornado.web import Application, HTTPError

from benchmarks.tornado.with_fastopenapi.schemas import (
    RecordCreate,
    RecordResponse,
    RecordUpdate,
)
from benchmarks.tornado.with_fastopenapi.storage import RecordStore
from fastopenapi.routers import TornadoRouter

# Initialize Sanic app and router
app = Application()
router = TornadoRouter(
    app=app,
    title="Record API",
    description="A simple Record API built with FastOpenAPI and Tornado",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Initialize the storage
store = RecordStore()


# Define routes using the TornadoRouter decorators
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
        raise HTTPError(status_code=404, log_message="Not Found")
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
        raise HTTPError(status_code=404, log_message="Not Found")

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
        raise HTTPError(status_code=404, log_message="Not Found")
    return updated_record


@router.delete("/records/{record_id}", tags=["records"], status_code=204)
async def delete_record(record_id: str):
    """
    Delete a record
    """
    if not store.delete(record_id):
        raise HTTPError(status_code=404, log_message="Not Found")
    return None


async def main():
    app.listen(8001)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
