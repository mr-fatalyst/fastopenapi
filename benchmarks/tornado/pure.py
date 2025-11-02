import asyncio
import json

import tornado.ioloop
import tornado.web

from benchmarks.common import RecordStore

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
        """Get all records"""
        records = store.get_all()
        self.set_status(200)
        self.write(json.dumps(records))

    def post(self):
        """Create a new record"""
        try:
            data = json.loads(self.request.body)
            new_record = store.create(data)
            self.set_status(201)
            self.write(json.dumps(new_record))
        except ValueError as e:
            self.set_status(400)
            self.write(json.dumps({"error": str(e)}))


class RecordDetailHandler(BaseRecordHandler):
    """Handle /records/{record_id} endpoint"""

    def get(self, record_id):
        """Get a specific record by ID"""
        record = store.get_by_id(record_id)
        if record:
            self.set_status(200)
            self.write(json.dumps(record))
        else:
            self.set_status(404)
            self.write(json.dumps({"error": "Record not found"}))

    def put(self, record_id):
        """Replace a record completely"""
        try:
            if not store.get_by_id(record_id):
                self.set_status(404)
                self.write(json.dumps({"error": "Record not found"}))
                return

            data = json.loads(self.request.body)
            store.delete(record_id)
            record = {"id": record_id, **data}
            store.records[record_id] = record
            self.set_status(200)
            self.write(json.dumps(record))
        except ValueError as e:
            self.set_status(400)
            self.write(json.dumps({"error": str(e)}))

    def patch(self, record_id):
        """Update a record partially"""
        try:
            data = json.loads(self.request.body)
            updated_record = store.update(record_id, data)
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
        """Delete a record"""
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
    app.listen(8000)
    print("Tornado server started on http://127.0.0.1:8000")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
