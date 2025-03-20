from http import HTTPStatus

from flask import Flask, abort

from benchmarks.flask.with_fastopenapi.schemas import (
    RecordCreate,
    RecordResponse,
    RecordUpdate,
)
from benchmarks.flask.with_fastopenapi.storage import RecordStore
from fastopenapi.routers import FlaskRouter

# Initialize Flask app and router
app = Flask(__name__)
router = FlaskRouter(
    app=app,
    title="Record API",
    description="A simple Record API built with FastOpenAPI and Flask",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Initialize the storage
store = RecordStore()


# Define routes using the FlaskRouter decorators
@router.get("/records", tags=["records"], response_model=list[RecordResponse])
def get_records():
    """
    Get all records
    """
    return store.get_all()


@router.get("/records/{record_id}", tags=["records"], response_model=RecordResponse)
def get_record(record_id: str):
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
def create_record(record: RecordCreate):
    """
    Create a new record
    """
    return store.create(record)


@router.put("/records/{record_id}", tags=["records"], response_model=RecordResponse)
def update_record_full(record_id: str, record: RecordCreate):
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
    return RecordResponse(**new_record)


@router.patch("/records/{record_id}", tags=["records"], response_model=RecordResponse)
def update_record_partial(record_id: str, record: RecordUpdate):
    """
    Update a record partially (only specified fields)
    """
    updated_record = store.update(record_id, record)
    if not updated_record:
        abort(HTTPStatus.NOT_FOUND)
    return updated_record


@router.delete("/records/{record_id}", tags=["records"], status_code=204)
def delete_record(record_id: str):
    """
    Delete a record
    """
    if not store.delete(record_id):
        abort(HTTPStatus.NOT_FOUND)
    return None


if __name__ == "__main__":
    app.run(port=8001)
