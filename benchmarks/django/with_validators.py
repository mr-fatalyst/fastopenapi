import json
import logging
import os

import django
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from benchmarks.common import RecordCreate, RecordResponse, RecordStore, RecordUpdate

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

store = RecordStore()


@csrf_exempt
def get_all_records(request):
    """Get all records with response validation"""
    if request.method == "GET":
        records = store.get_all()
        records = [RecordResponse(**r) for r in records]
        return JsonResponse([record.model_dump() for record in records], safe=False)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def get_one_record(request, record_id):
    """Get one record with response validation"""
    if request.method == "GET":
        record = store.get_by_id(record_id)
        if not record:
            return JsonResponse({"error": "Record not found"}, status=404)
        record = RecordResponse(**record)
        return JsonResponse(record.model_dump())
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def create_record(request):
    """Create record with input validation"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            record_data = RecordCreate(**data)
            new_record = store.create(record_data.model_dump())
            return JsonResponse(new_record, status=201)
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def replace_record(request, record_id):
    """Replace record with input and output validation"""
    if request.method == "PUT":
        if not store.get_by_id(record_id):
            return JsonResponse({"error": "Record not found"}, status=404)
        try:
            data = json.loads(request.body)
            record_data = RecordCreate(**data)
            store.delete(record_id)
            record = {"id": record_id, **record_data.model_dump()}
            store.records[record_id] = record
            return JsonResponse(RecordResponse(**record).model_dump())
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def update_record(request, record_id):
    """Update record partially with input validation"""
    if request.method == "PATCH":
        try:
            data = json.loads(request.body)
            record_data = RecordUpdate(**data)
            updated_record = store.update(
                record_id, record_data.model_dump(exclude_unset=True)
            )
            if updated_record:
                return JsonResponse(updated_record)
            else:
                return JsonResponse({"error": "Record not found"}, status=404)
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def delete_record(request, record_id):
    """Delete record by ID"""
    if request.method == "DELETE":
        if store.delete(record_id):
            return HttpResponse(status=204)
        else:
            return JsonResponse({"error": "Record not found"}, status=404)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def reset_store(request):
    """Reset store for benchmarking"""
    store.clear()
    return HttpResponse(status=204)


@csrf_exempt
def technical_handler(request):
    """Handle technical endpoints"""
    if request.method == "POST":
        return reset_store(request)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def records_handler(request):
    """Handle /records endpoint"""
    if request.method == "GET":
        return get_all_records(request)
    elif request.method == "POST":
        return create_record(request)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def record_detail_handler(request, record_id):
    """Handle /records/{id} endpoint"""
    if request.method == "GET":
        return get_one_record(request, record_id)
    elif request.method == "PUT":
        return replace_record(request, record_id)
    elif request.method == "PATCH":
        return update_record(request, record_id)
    elif request.method == "DELETE":
        return delete_record(request, record_id)
    return JsonResponse({"error": "Method not allowed"}, status=405)


urlpatterns = [
    path("__reset", technical_handler),
    path("records", records_handler),
    path("records/<str:record_id>", record_detail_handler),
]

if __name__ == "__main__":
    from django.core.management import execute_from_command_line

    execute_from_command_line(
        ["manage.py", "runserver", "127.0.0.1:8001", "--noreload", "--nothreading"]
    )
