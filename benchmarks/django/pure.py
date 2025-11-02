import json
import logging
import os

import django
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from benchmarks.common import RecordStore

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
    if request.method == "GET":
        records = store.get_all()
        return JsonResponse(records, safe=False)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def get_one_record(request, record_id):
    if request.method == "GET":
        record = store.get_by_id(record_id)
        if record:
            return JsonResponse(record)
        else:
            return JsonResponse({"error": "Record not found"}, status=404)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def create_record(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            new_record = store.create(data)
            return JsonResponse(new_record, status=201)
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def replace_record(request, record_id):
    if request.method == "PUT":
        if not store.get_by_id(record_id):
            return JsonResponse({"error": "Record not found"}, status=404)
        try:
            data = json.loads(request.body)
            store.delete(record_id)
            record = {"id": record_id, **data}
            store.records[record_id] = record
            return JsonResponse(record)
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def update_record(request, record_id):
    if request.method == "PATCH":
        try:
            data = json.loads(request.body)
            updated_record = store.update(record_id, data)
            if updated_record:
                return JsonResponse(updated_record)
            else:
                return JsonResponse({"error": "Record not found"}, status=404)
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def delete_record(request, record_id):
    if request.method == "DELETE":
        if store.delete(record_id):
            return HttpResponse(status=204)
        else:
            return JsonResponse({"error": "Record not found"}, status=404)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def reset_store(request):
    store.clear()
    return HttpResponse(status=204)


@csrf_exempt
def technical_handler(request):
    if request.method == "POST":
        return reset_store(request)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def records_handler(request):
    if request.method == "GET":
        return get_all_records(request)
    elif request.method == "POST":
        return create_record(request)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def record_detail_handler(request, record_id):
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
        ["manage.py", "runserver", "127.0.0.1:8000", "--noreload", "--nothreading"]
    )
