from sanic import Sanic, json
from sanic.response import empty

from benchmarks.common import RecordStore

app = Sanic(__name__, configure_logging=False)
store = RecordStore()


@app.get("/records")
async def get_all_records(request):
    return json(store.get_all(), status=200)


@app.get("/records/<record_id>")
async def get_one_record(request, record_id):
    record = store.get_by_id(record_id)
    if record:
        return json(record, status=200)
    else:
        return json({"error": "Record not found"}, status=404)


@app.post("/records")
async def create_record(request):
    try:
        new_record = store.create(request.json)
        return json(new_record, status=201)
    except ValueError as e:
        return json({"error": str(e)}, status=400)


@app.put("/records/<record_id>")
async def replace_record(request, record_id):
    try:
        if not store.get_by_id(record_id):
            return json({"error": "Record not found"}, status=404)

        data = request.json
        store.delete(record_id)
        record = {"id": record_id, **data}
        store.records[record_id] = record
        return json(record, status=200)
    except ValueError as e:
        return json({"error": str(e)}, status=400)


@app.patch("/records/<record_id>")
async def update_record(request, record_id):
    try:
        data = request.json
        updated_record = store.update(record_id, data)
        if updated_record:
            return json(updated_record, status=200)
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


@app.post("/__reset")
async def reset_store(request):
    store.clear()
    return None


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
