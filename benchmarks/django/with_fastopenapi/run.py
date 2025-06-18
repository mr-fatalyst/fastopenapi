import uvicorn
from django.conf import settings
from django.core.asgi import get_asgi_application
from django.http import Http404
from django.urls import path

from benchmarks.django.with_fastopenapi.schemas import (
    RecordCreate,
    RecordResponse,
    RecordUpdate,
)
from benchmarks.django.with_fastopenapi.storage import RecordStore
from fastopenapi.routers import DjangoRouter

# Initialize Django app and router
settings.configure(
    DEBUG=False,
    ALLOWED_HOSTS=["127.0.0.1"],
    SECRET_KEY="__CHANGEME__",
    ROOT_URLCONF=__name__,
)
application = get_asgi_application()
router = DjangoRouter(
    app=True,
    title="Record API",
    description="A simple Record API built with FastOpenAPI and Django",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Initialize the storage
store = RecordStore()


# Define routes using the DjangoRouter decorators
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
        raise Http404("Record not found")
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
        raise Http404("Record not found")

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
        raise Http404("Record not found")
    return updated_record


@router.delete("/records/{record_id}", tags=["records"], status_code=204)
def delete_record(record_id: str):
    """
    Delete a record
    """
    if not store.delete(record_id):
        raise Http404("Record not found")
    return None


urlpatterns = [path("", router.urls)]

if __name__ == "__main__":
    uvicorn.run(application, host="127.0.0.1", port=8001)
