import asyncio

import tornado.ioloop
import tornado.web

from benchmarks.common import RecordCreate, RecordResponse, RecordStore, RecordUpdate
from fastopenapi.routers import TornadoRouter

# Initialize Tornado app
app = tornado.web.Application()

# Initialize router
router = TornadoRouter(
    app=app,
    title="Record API",
    description="A simple Record API built with FastOpenAPI and Tornado",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

store = RecordStore()


@router.get("/records", tags=["records"], response_model=list[RecordResponse])
async def get_records():
    """Get all records"""
    return store.get_all()


@router.get("/records/{record_id}", tags=["records"], response_model=RecordResponse)
async def get_record(record_id: str):
    """Get a specific record by ID"""
    record = store.get_by_id(record_id)
    if not record:
        raise tornado.web.HTTPError(404, reason="Not Found")
    return record


@router.post(
    "/records", tags=["records"], status_code=201, response_model=RecordResponse
)
async def create_record(record: RecordCreate):
    """Create a new record"""
    return store.create(record.model_dump())


@router.put("/records/{record_id}", tags=["records"], response_model=RecordResponse)
async def update_record_full(record_id: str, record: RecordCreate):
    """Update a record completely (all fields required)"""
    existing_record = store.get_by_id(record_id)
    if not existing_record:
        raise tornado.web.HTTPError(404, reason="Not Found")

    store.delete(record_id)
    new_record = {"id": record_id, **record.model_dump()}
    store.records[record_id] = new_record
    return new_record


@router.patch("/records/{record_id}", tags=["records"], response_model=RecordResponse)
async def update_record_partial(record_id: str, record: RecordUpdate):
    """Update a record partially (only specified fields)"""
    updated_record = store.update(record_id, record.model_dump(exclude_unset=True))
    if not updated_record:
        raise tornado.web.HTTPError(404, reason="Not Found")
    return updated_record


@router.delete("/records/{record_id}", tags=["records"], status_code=204)
async def delete_record(record_id: str):
    """Delete a record"""
    if not store.delete(record_id):
        raise tornado.web.HTTPError(404, reason="Not Found")
    return None


@router.post("/__reset", tags=["records"], status_code=204)
async def reset_store():
    """Reset store for benchmarking"""
    store.clear()
    return None


async def main():
    app.listen(8002)
    print("Tornado server started on http://127.0.0.1:8002")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
