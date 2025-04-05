from aiohttp import web

from benchmarks.aiohttp.without_fastopenapi.schemas import (
    RecordCreate,
    RecordResponse,
    RecordUpdate,
)
from benchmarks.aiohttp.without_fastopenapi.storage import RecordStore

store = RecordStore()


async def get_all_records(request: web.Request):
    records = store.get_all()
    return web.json_response([record.model_dump() for record in records], status=200)


async def get_one_record(request: web.Request):
    record_id = request.match_info.get("record_id")
    record = store.get_by_id(record_id)
    if record:
        return web.json_response(record.model_dump(), status=200)
    else:
        return web.json_response({"error": "Record not found"}, status=404)


async def create_record(request: web.Request):
    try:
        data = await request.json()
        record_data = RecordCreate(**data)
        new_record = store.create(record_data)
        return web.json_response(new_record.model_dump(), status=201)
    except ValueError as e:
        return web.json_response({"error": str(e)}, status=400)


async def replace_record(request: web.Request):
    record_id = request.match_info.get("record_id")
    if not store.get_by_id(record_id):
        return web.json_response({"error": "Record not found"}, status=404)
    try:
        data = await request.json()
        record_data = RecordCreate(**data)
        store.delete(record_id)
        record = {"id": record_id, **record_data.model_dump()}
        store.records[record_id] = record
        return web.json_response(RecordResponse(**record).model_dump(), status=200)
    except ValueError as e:
        return web.json_response({"error": str(e)}, status=400)


async def update_record(request: web.Request):
    record_id = request.match_info.get("record_id")
    try:
        data = await request.json()
        record_data = RecordUpdate(**data)
        updated_record = store.update(record_id, record_data)
        if updated_record:
            return web.json_response(updated_record.model_dump(), status=200)
        else:
            return web.json_response({"error": "Record not found"}, status=404)
    except ValueError as e:
        return web.json_response({"error": str(e)}, status=400)


async def delete_record(request: web.Request):
    record_id = request.match_info.get("record_id")
    if store.delete(record_id):
        return web.Response(status=204)
    else:
        return web.json_response({"error": "Record not found"}, status=404)


app = web.Application()
app.router.add_get("/records", get_all_records)
app.router.add_get("/records/{record_id}", get_one_record)
app.router.add_post("/records", create_record)
app.router.add_put("/records/{record_id}", replace_record)
app.router.add_patch("/records/{record_id}", update_record)
app.router.add_delete("/records/{record_id}", delete_record)

if __name__ == "__main__":
    web.run_app(app, host="127.0.0.1", port=8000)
