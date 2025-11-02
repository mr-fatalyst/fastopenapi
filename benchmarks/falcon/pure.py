import falcon
from waitress import serve

from benchmarks.common import RecordStore

store = RecordStore()


class RecordsResource:
    """Handle /records endpoint"""

    def on_get(self, req, resp):
        """Get all records"""
        records = store.get_all()
        resp.media = records
        resp.status = falcon.HTTP_200

    def on_post(self, req, resp):
        """Create a new record"""
        try:
            data = req.media
            new_record = store.create(data)
            resp.media = new_record
            resp.status = falcon.HTTP_201
        except ValueError as e:
            resp.media = {"error": str(e)}
            resp.status = falcon.HTTP_400


class RecordDetailResource:
    """Handle /records/{record_id} endpoint"""

    def on_get(self, req, resp, record_id):
        """Get a specific record by ID"""
        record = store.get_by_id(record_id)
        if record:
            resp.media = record
            resp.status = falcon.HTTP_200
        else:
            resp.media = {"error": "Record not found"}
            resp.status = falcon.HTTP_404

    def on_put(self, req, resp, record_id):
        """Replace a record completely"""
        try:
            if not store.get_by_id(record_id):
                resp.media = {"error": "Record not found"}
                resp.status = falcon.HTTP_404
                return

            data = req.media
            store.delete(record_id)
            record = {"id": record_id, **data}
            store.records[record_id] = record
            resp.media = record
            resp.status = falcon.HTTP_200
        except ValueError as e:
            resp.media = {"error": str(e)}
            resp.status = falcon.HTTP_400

    def on_patch(self, req, resp, record_id):
        """Update a record partially"""
        try:
            data = req.media
            updated_record = store.update(record_id, data)
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
        """Delete a record"""
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
    print("Falcon server started on http://127.0.0.1:8000")
    serve(app, host="127.0.0.1", port=8000, threads=1, _quiet=True)
