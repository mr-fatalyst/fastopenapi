from wsgiref import simple_server

import falcon
from waitress import serve

from benchmarks.common import RecordCreate, RecordResponse, RecordStore, RecordUpdate

store = RecordStore()


class QuietHandler(simple_server.WSGIRequestHandler):
    def log_message(self, format, *args):
        pass


class RecordsResource:
    """Handle /records endpoint"""

    def on_get(self, req, resp):
        """Get all records with response validation"""
        records = store.get_all()
        records = [RecordResponse(**r) for r in records]
        resp.media = [record.model_dump() for record in records]
        resp.status = falcon.HTTP_200

    def on_post(self, req, resp):
        """Create a new record with input validation"""
        try:
            data = req.media
            record_data = RecordCreate(**data)
            new_record = store.create(record_data.model_dump())
            resp.media = new_record
            resp.status = falcon.HTTP_201
        except ValueError as e:
            resp.media = {"error": str(e)}
            resp.status = falcon.HTTP_400


class RecordDetailResource:
    """Handle /records/{record_id} endpoint"""

    def on_get(self, req, resp, record_id):
        """Get a specific record by ID with response validation"""
        record = store.get_by_id(record_id)
        if not record:
            resp.media = {"error": "Record not found"}
            resp.status = falcon.HTTP_404
            return
        record = RecordResponse(**record)
        resp.media = record.model_dump()
        resp.status = falcon.HTTP_200

    def on_put(self, req, resp, record_id):
        """Replace a record completely with input and output validation"""
        try:
            if not store.get_by_id(record_id):
                resp.media = {"error": "Record not found"}
                resp.status = falcon.HTTP_404
                return

            data = req.media
            record_data = RecordCreate(**data)
            store.delete(record_id)
            record = {"id": record_id, **record_data.model_dump()}
            store.records[record_id] = record
            resp.media = RecordResponse(**record).model_dump()
            resp.status = falcon.HTTP_200
        except ValueError as e:
            resp.media = {"error": str(e)}
            resp.status = falcon.HTTP_400

    def on_patch(self, req, resp, record_id):
        """Update a record partially with input validation"""
        try:
            data = req.media
            record_data = RecordUpdate(**data)
            updated_record = store.update(
                record_id, record_data.model_dump(exclude_unset=True)
            )
            if updated_record:
                resp.media = updated_record
                resp.status = falcon.HTTP_200
            else:
                resp.media = {"error": "Record not found"}
                resp.status = falcon.HTTP_404
        except ValueError as e:
            resp.media = {"error": str(e)}
            resp.status = falcon.HTTP_400

    def on_delete(self, req, resp, record_id):
        """Delete a record by ID"""
        if store.delete(record_id):
            resp.status = falcon.HTTP_204
        else:
            resp.media = {"error": "Record not found"}
            resp.status = falcon.HTTP_404


class ResetResource:
    """Handle /__reset endpoint"""

    def on_post(self, req, resp):
        """Reset store for benchmarking"""
        store.clear()
        resp.status = falcon.HTTP_204


# Create Falcon app
app = falcon.App()

# Add routes
app.add_route("/records", RecordsResource())
app.add_route("/records/{record_id}", RecordDetailResource())
app.add_route("/__reset", ResetResource())

if __name__ == "__main__":
    print("Falcon server started on http://127.0.0.1:8001")
    serve(app, host="127.0.0.1", port=8001, threads=1, _quiet=True)
