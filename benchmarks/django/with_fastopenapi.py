import logging
import os

import django
from django.conf import settings
from django.http import Http404

from benchmarks.common import RecordCreate, RecordResponse, RecordStore, RecordUpdate
from fastopenapi.routers import DjangoRouter

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "__main__")
logging.disable(logging.CRITICAL)

if not settings.configured:
    settings.configure(
        DEBUG=False,
        SECRET_KEY="benchmark-secret-key",
        ROOT_URLCONF=__name__,
        ALLOWED_HOSTS=["*"],
        MIDDLEWARE=[
            "django.middleware.common.CommonMiddleware",
        ],
        USE_TZ=True,
        APPEND_SLASH=False,
    )
    django.setup()

router = DjangoRouter(
    title="Record API",
    description="A simple Record API built with FastOpenAPI and Django",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

store = RecordStore()


@router.get("/records", tags=["records"], response_model=list[RecordResponse])
def get_records():
    """Get all records"""
    return store.get_all()


@router.get("/records/{record_id}", tags=["records"], response_model=RecordResponse)
def get_record(record_id: str):
    """Get a specific record by ID"""
    record = store.get_by_id(record_id)
    if not record:
        raise Http404("Not Found")
    return record


@router.post(
    "/records", tags=["records"], status_code=201, response_model=RecordResponse
)
def create_record(record: RecordCreate):
    """Create a new record"""
    return store.create(record.model_dump())


@router.put("/records/{record_id}", tags=["records"], response_model=RecordResponse)
def update_record_full(record_id: str, record: RecordCreate):
    """Update a record completely (all fields required)"""
    existing_record = store.get_by_id(record_id)
    if not existing_record:
        raise Http404("Not Found")

    store.delete(record_id)
    new_record = {"id": record_id, **record.model_dump()}
    store.records[record_id] = new_record
    return new_record


@router.patch("/records/{record_id}", tags=["records"], response_model=RecordResponse)
def update_record_partial(record_id: str, record: RecordUpdate):
    """Update a record partially (only specified fields)"""
    updated_record = store.update(record_id, record.model_dump(exclude_unset=True))
    if not updated_record:
        raise Http404("Not Found")
    return updated_record


@router.delete("/records/{record_id}", tags=["records"], status_code=204)
def delete_record(record_id: str):
    """Delete a record"""
    if not store.delete(record_id):
        raise Http404("Not Found")
    return None


@router.post("/__reset", tags=["records"], status_code=204)
def reset_store():
    store.clear()
    return None


urlpatterns = router.urls[0]

if __name__ == "__main__":
    from django.core.management import execute_from_command_line

    execute_from_command_line(
        ["manage.py", "runserver", "127.0.0.1:8002", "--noreload", "--nothreading"]
    )
