import logging
from http import HTTPStatus

from quart import Quart, abort

from benchmarks.common.schemas import (
    RecordCreate,
    RecordResponse,
    RecordUpdate,
)
from benchmarks.common.storage import RecordStore
from fastopenapi.routers import QuartRouter

# Initialize Quart app and router
app = Quart(__name__)
router = QuartRouter(
    app=app,
    title="Record API",
    description="A simple Record API built with FastOpenAPI and Quart",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

logging.getLogger("quart.app").disabled = True
logging.getLogger("quart.serving").disabled = True
logging.getLogger("hypercorn.error").disabled = True
logging.getLogger("hypercorn.access").disabled = True


# Initialize the storage
store = RecordStore()


# Define routes using the QuartRouter decorators
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
        abort(HTTPStatus.NOT_FOUND)
    return record


@router.post(
    "/records", tags=["records"], status_code=201, response_model=RecordResponse
)
async def create_record(record: RecordCreate):
    """
    Create a new record
    """
    return store.create(record.model_dump())


@router.put("/records/{record_id}", tags=["records"], response_model=RecordResponse)
async def update_record_full(record_id: str, record: RecordCreate):
    """
    Update a record completely (all fields required)
    """
    existing_record = store.get_by_id(record_id)
    if not existing_record:
        abort(HTTPStatus.NOT_FOUND)

    # Delete and recreate with the same ID
    store.delete(record_id)
    new_record = {"id": record_id, **record.model_dump()}
    store.records[record_id] = new_record
    return new_record


@router.patch("/records/{record_id}", tags=["records"], response_model=RecordResponse)
async def update_record_partial(record_id: str, record: RecordUpdate):
    """
    Update a record partially (only specified fields)
    """
    updated_record = store.update(record_id, record.model_dump(exclude_unset=True))
    if not updated_record:
        abort(HTTPStatus.NOT_FOUND)
    return updated_record


@router.delete("/records/{record_id}", tags=["records"], status_code=204)
async def delete_record(record_id: str):
    """
    Delete a record
    """
    if not store.delete(record_id):
        abort(HTTPStatus.NOT_FOUND)
    return None


@router.post("/__reset", tags=["records"], status_code=204)
async def reset_store():
    store.clear()
    return None


if __name__ == "__main__":
    app.run(port=8002)
