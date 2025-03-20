import json

import tornado.ioloop
import tornado.web
from tornado.web import RequestHandler

from benchmarks.sanic.without_fastopenapi.schemas import (
    RecordCreate,
    RecordResponse,
    RecordUpdate,
)
from benchmarks.sanic.without_fastopenapi.storage import RecordStore

store = RecordStore()


class BaseRecordHandler(RequestHandler):
    def set_default_headers(self):
        self.set_header("Content-Type", "application/json")

    def write_error(self, status_code, **kwargs):
        self.set_header("Content-Type", "application/json")
        self.finish(json.dumps({"error": self._reason}))


class RecordsHandler(BaseRecordHandler):
    def get(self):
        """Получить все записи (эквивалент @app.get("/records"))"""
        records = store.get_all()
        self.write(json.dumps([record.model_dump() for record in records]))

    def post(self):
        """Создать новую запись (эквивалент @app.post("/records"))"""
        try:
            data = json.loads(self.request.body)
            record_data = RecordCreate(**data)
            new_record = store.create(record_data)
            self.set_status(201)
            self.write(json.dumps(new_record.model_dump()))
        except ValueError as e:
            self.set_status(400)
            self.write(json.dumps({"error": str(e)}))


class RecordHandler(BaseRecordHandler):
    def get(self, record_id):
        """Получить конкретную запись (эквивалент @app.get("/records/<record_id>"))"""
        record = store.get_by_id(record_id)
        if record:
            self.write(json.dumps(record.model_dump()))
        else:
            self.set_status(404)
            self.write(json.dumps({"error": "Record not found"}))

    def put(self, record_id):
        """Заменить запись (эквивалент @app.put("/records/<record_id>"))"""
        try:
            if not store.get_by_id(record_id):
                self.set_status(404)
                self.write(json.dumps({"error": "Record not found"}))
                return

            data = json.loads(self.request.body)
            record_data = RecordCreate(**data)
            store.delete(record_id)
            record = {"id": record_id, **record_data.model_dump()}
            store.records[record_id] = record
            self.write(json.dumps(RecordResponse(**record).model_dump()))
        except ValueError as e:
            self.set_status(400)
            self.write(json.dumps({"error": str(e)}))

    def patch(self, record_id):
        """Обновить запись частично (эквивалент @app.patch("/records/<record_id>"))"""
        try:
            data = json.loads(self.request.body)
            record_data = RecordUpdate(**data)
            updated_record = store.update(record_id, record_data)
            if updated_record:
                self.write(json.dumps(updated_record.model_dump()))
            else:
                self.set_status(404)
                self.write(json.dumps({"error": "Record not found"}))
        except ValueError as e:
            self.set_status(400)
            self.write(json.dumps({"error": str(e)}))

    def delete(self, record_id):
        """Удалить запись (эквивалент @app.delete("/records/<record_id>"))"""
        if store.delete(record_id):
            self.set_status(204)
            self.finish()
        else:
            self.set_status(404)
            self.write(json.dumps({"error": "Record not found"}))


def make_app():
    return tornado.web.Application(
        [
            (r"/records", RecordsHandler),  # Обрабатывает GET и POST для /records
            (r"/records/([^/]+)", RecordHandler),
            # Обрабатывает GET, PUT, PATCH, DELETE для /records/<id>
        ]
    )


if __name__ == "__main__":
    app = make_app()
    app.listen(8000)
    print("Server started at http://localhost:8000")
    tornado.ioloop.IOLoop.current().start()
