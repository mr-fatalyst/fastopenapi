import falcon.asgi
import uvicorn

from benchmarks.falcon.without_fastopenapi.schemas import (
    RecordCreate,
    RecordResponse,
    RecordUpdate,
)
from benchmarks.falcon.without_fastopenapi.storage import RecordStore


class RecordResource:
    def __init__(self, store: RecordStore):
        self.store = store

    async def on_get(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response, record_id=None
    ):
        if record_id:
            record = self.store.get_by_id(record_id)
            if record:
                resp.media = record.model_dump()
                resp.status = falcon.HTTP_200
            else:
                resp.media = {"error": "Record not found"}
                resp.status = falcon.HTTP_404
        else:
            records = self.store.get_all()
            resp.media = [record.model_dump() for record in records]
            resp.status = falcon.HTTP_200

    async def on_post(self, req: falcon.asgi.Request, resp: falcon.asgi.Response):
        try:
            data = await req.get_media()
            record_data = RecordCreate(**data)
            new_record = self.store.create(record_data)
            resp.media = new_record.model_dump()
            resp.status = falcon.HTTP_201
        except ValueError as e:
            resp.media = {"error": str(e)}
            resp.status = falcon.HTTP_400

    async def on_put(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response, record_id
    ):
        try:
            if not self.store.get_by_id(record_id):
                resp.media = {"error": "Record not found"}
                resp.status = falcon.HTTP_404
                return

            data = await req.get_media()
            record_data = RecordCreate(**data)
            self.store.delete(record_id)
            record = {"id": record_id, **record_data.model_dump()}
            self.store.records[record_id] = record
            resp.media = RecordResponse(**record).model_dump()
            resp.status = falcon.HTTP_200
        except ValueError as e:
            resp.media = {"error": str(e)}
            resp.status = falcon.HTTP_400

    async def on_patch(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response, record_id
    ):
        try:
            data = await req.get_media()
            record_data = RecordUpdate(**data)
            updated_record = self.store.update(record_id, record_data)
            if updated_record:
                resp.media = updated_record.model_dump()
                resp.status = falcon.HTTP_200
            else:
                resp.media = {"error": "Record not found"}
                resp.status = falcon.HTTP_404
        except ValueError as e:
            resp.media = {"error": str(e)}
            resp.status = falcon.HTTP_400

    async def on_delete(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response, record_id
    ):
        if self.store.delete(record_id):
            resp.status = falcon.HTTP_204
        else:
            resp.media = {"error": "Record not found"}
            resp.status = falcon.HTTP_404


store = RecordStore()
app = falcon.asgi.App()
record_resource = RecordResource(store)

app.add_route("/records", record_resource)
app.add_route("/records/{record_id}", record_resource)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
