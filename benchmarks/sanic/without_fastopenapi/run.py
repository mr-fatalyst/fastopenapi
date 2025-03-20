from sanic import Sanic, json
from sanic.response import empty

from benchmarks.sanic.without_fastopenapi.schemas import (
    RecordCreate,
    RecordResponse,
    RecordUpdate,
)
from benchmarks.sanic.without_fastopenapi.storage import RecordStore

app = Sanic("records_api")
store = RecordStore()


@app.get("/records")
async def get_all_records(request):
    records = store.get_all()
    return json([record.model_dump() for record in records], status=200)


@app.get("/records/<record_id>")
async def get_one_record(request, record_id):
    record = store.get_by_id(record_id)
    if record:
        return json(record.model_dump(), status=200)
    else:
        return json({"error": "Record not found"}, status=404)


@app.post("/records")
async def create_record(request):
    try:
        data = request.json
        record_data = RecordCreate(**data)
        new_record = store.create(record_data)
        return json(new_record.model_dump(), status=201)
    except ValueError as e:
        return json({"error": str(e)}, status=400)


@app.put("/records/<record_id>")
async def replace_record(request, record_id):
    try:
        if not store.get_by_id(record_id):
            return json({"error": "Record not found"}, status=404)

        data = request.json
        record_data = RecordCreate(**data)
        store.delete(record_id)
        record = {"id": record_id, **record_data.model_dump()}
        store.records[record_id] = record
        return json(RecordResponse(**record).model_dump(), status=200)
    except ValueError as e:
        return json({"error": str(e)}, status=400)


@app.patch("/records/<record_id>")
async def update_record(request, record_id):
    try:
        data = request.json
        record_data = RecordUpdate(**data)
        updated_record = store.update(record_id, record_data)
        if updated_record:
            return json(updated_record.model_dump(), status=200)
        else:
            return json({"error": "Record not found"}, status=404)
    except ValueError as e:
        return json({"error": str(e)}, status=400)


@app.delete("/records/<record_id>")
async def delete_record(request, record_id):
    if store.delete(record_id):
        return empty(status=204)
    else:
        return json({"error": "Record not found"}, status=404)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, fast=True)
