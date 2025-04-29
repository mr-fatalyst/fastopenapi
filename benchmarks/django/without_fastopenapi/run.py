import json
from http import HTTPStatus

import uvicorn
from django.conf import settings
from django.core.asgi import get_asgi_application
from django.http import HttpRequest, HttpResponse
from django.http.response import JsonResponse
from django.urls import path
from django.views import View

from benchmarks.django.without_fastopenapi.schemas import (
    RecordCreate,
    RecordResponse,
    RecordUpdate,
)
from benchmarks.django.without_fastopenapi.storage import RecordStore

store = RecordStore()


class RecordView(View):
    def get(self, req: HttpRequest) -> HttpResponse:
        records = store.get_all()
        return JsonResponse(
            [record.model_dump() for record in records],
            status=HTTPStatus.OK,
            safe=False,
        )

    def post(self, req: HttpRequest) -> HttpResponse:
        try:
            data = json.load(req)
            record_data = RecordCreate(**data)
            new_record = store.create(record_data)
            return JsonResponse(new_record.model_dump(), status=HTTPStatus.CREATED)
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=HTTPStatus.BAD_REQUEST)


class RecordDetailView(View):
    def get(self, req: HttpRequest, record_id) -> HttpResponse:
        record = store.get_by_id(record_id)
        if record:
            return JsonResponse(record.model_dump(), status=HTTPStatus.OK)
        else:
            return JsonResponse(
                {"error": "Record not found"}, status=HTTPStatus.NOT_FOUND
            )

    def put(self, req: HttpRequest, record_id) -> HttpResponse:
        try:
            if not store.get_by_id(record_id):
                return JsonResponse(
                    {"error": "Record not found"}, status=HTTPStatus.NOT_FOUND
                )

            data = json.load(req)
            record_data = RecordCreate(**data)
            store.delete(record_id)
            record = {"id": record_id, **record_data.model_dump()}
            store.records[record_id] = record
            return JsonResponse(
                RecordResponse(**record).model_dump(), status=HTTPStatus.OK
            )
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=HTTPStatus.BAD_REQUEST)

    def patch(self, req: HttpRequest, record_id) -> HttpResponse:
        try:
            data = json.load(req)
            record_data = RecordUpdate(**data)
            updated_record = store.update(record_id, record_data)
            if updated_record:
                return JsonResponse(updated_record.model_dump(), status=HTTPStatus.OK)
            else:
                return JsonResponse(
                    {"error": "Record not found"}, status=HTTPStatus.NOT_FOUND
                )
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=HTTPStatus.BAD_REQUEST)

    def delete(self, req: HttpRequest, record_id) -> HttpResponse:
        if store.delete(record_id):
            return HttpResponse(status=HTTPStatus.NO_CONTENT)
        else:
            return JsonResponse(
                {"error": "Record not found"}, status=HTTPStatus.NOT_FOUND
            )


settings.configure(
    DEBUG=False,
    ALLOWED_HOSTS=["127.0.0.1"],
    SECRET_KEY="__CHANGEME__",
    ROOT_URLCONF=__name__,
)
application = get_asgi_application()

urlpatterns = [
    path("records", RecordView.as_view()),
    path("records/<record_id>", RecordDetailView.as_view()),
]


if __name__ == "__main__":
    uvicorn.run(application, host="127.0.0.1", port=8000)
