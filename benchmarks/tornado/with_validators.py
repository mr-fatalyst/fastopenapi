import asyncio
import json

import tornado.ioloop
import tornado.web

from benchmarks.common import RecordCreate, RecordResponse, RecordStore, RecordUpdate

store = RecordStore()


class BaseRecordHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Content-Type", "application/json")

    def write_error(self, status_code, **kwargs):
        self.set_header("Content-Type", "application/json")
        self.finish(json.dumps({"error": self._reason}))


class RecordsHandler(BaseRecordHandler):
    """Handle /records endpoint"""

    def get(self):
        """Get all records with response validation"""
        records = store.get_all()
        records = [RecordResponse(**r) for r in records]
        self.set_status(200)
        self.write(json.dumps([record.model_dump() for record in records]))

    def post(self):
        """Create a new record with input validation"""
        try:
            data = json.loads(self.request.body)
            record_data = RecordCreate(**data)
            new_record = store.create(record_data.model_dump())
            self.set_status(201)
            self.write(json.dumps(new_record))
        except ValueError as e:
            self.set_status(400)
            self.write(json.dumps({"error": str(e)}))


class RecordDetailHandler(BaseRecordHandler):
    """Handle /records/{record_id} endpoint"""

    def get(self, record_id):
        """Get a specific record by ID with response validation"""
        record = store.get_by_id(record_id)
        if not record:
            self.set_status(404)
            self.write(json.dumps({"error": "Record not found"}))
            return
        record = RecordResponse(**record)
        self.set_status(200)
        self.write(json.dumps(record.model_dump()))

    def put(self, record_id):
        """Replace a record completely with input and output validation"""
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
            self.set_status(200)
            self.write(json.dumps(RecordResponse(**record).model_dump()))
        except ValueError as e:
            self.set_status(400)
            self.write(json.dumps({"error": str(e)}))

    def patch(self, record_id):
        """Update a record partially with input validation"""
        try:
            data = json.loads(self.request.body)
            record_data = RecordUpdate(**data)
            updated_record = store.update(
                record_id, record_data.model_dump(exclude_unset=True)
            )
            if updated_record:
                self.set_status(200)
                self.write(json.dumps(updated_record))
            else:
                self.set_status(404)
                self.write(json.dumps({"error": "Record not found"}))
        except ValueError as e:
            self.set_status(400)
            self.write(json.dumps({"error": str(e)}))

    def delete(self, record_id):
        """Delete a record by ID"""
        if store.delete(record_id):
            self.set_status(204)
        else:
            self.set_status(404)
            self.write(json.dumps({"error": "Record not found"}))


class ResetHandler(tornado.web.RequestHandler):
    """Handle /__reset endpoint"""

    def post(self):
        """Reset store for benchmarking"""
        store.clear()
        self.set_status(204)


def make_app():
    return tornado.web.Application(
        [
            (r"/records", RecordsHandler),
            (r"/records/([^/]+)", RecordDetailHandler),
            (r"/__reset", ResetHandler),
        ]
    )


async def main():
    app = make_app()
    app.listen(8001)
    print("Tornado server started on http://127.0.0.1:8001")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
