import uvicorn
from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from benchmarks.common import RecordStore

store = RecordStore()


async def get_all_records(request):
    return JSONResponse(store.get_all())


async def get_one_record(request):
    record_id = request.path_params["record_id"]
    record = store.get_by_id(record_id)
    if record:
        return JSONResponse(record)
    else:
        return JSONResponse({"error": "Record not found"}, status_code=404)


async def create_record(request):
    try:
        data = await request.json()
        new_record = store.create(data)
        return JSONResponse(new_record, status_code=201)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)


async def replace_record(request):
    record_id = request.path_params["record_id"]
    if not store.get_by_id(record_id):
        return JSONResponse({"error": "Record not found"}, status_code=404)
    try:
        data = await request.json()
        store.delete(record_id)
        record = {"id": record_id, **data}
        store.records[record_id] = record
        return JSONResponse(record)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)


async def update_record(request):
    record_id = request.path_params["record_id"]
    try:
        data = await request.json()
        updated_record = store.update(record_id, data)
        if updated_record:
            return JSONResponse(updated_record)
        else:
            return JSONResponse({"error": "Record not found"}, status_code=404)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)


async def delete_record(request):
    record_id = request.path_params["record_id"]
    if store.delete(record_id):
        return Response(status_code=204)
    else:
        return JSONResponse({"error": "Record not found"}, status_code=404)


async def reset_store(request):
    store.clear()
    return Response(status_code=204)


routes = [
    Route("/records", get_all_records, methods=["GET"]),
    Route("/records/{record_id}", get_one_record, methods=["GET"]),
    Route("/records", create_record, methods=["POST"]),
    Route("/records/{record_id}", replace_record, methods=["PUT"]),
    Route("/records/{record_id}", update_record, methods=["PATCH"]),
    Route("/records/{record_id}", delete_record, methods=["DELETE"]),
    Route("/__reset", reset_store, methods=["POST"]),
]

app = Starlette(routes=routes)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")
