import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from benchmarks.starlette.without_fastopenapi.schemas import (
    RecordCreate,
    RecordResponse,
    RecordUpdate,
)
from benchmarks.starlette.without_fastopenapi.storage import RecordStore

store = RecordStore()


async def get_all_records(request: Request):
    records = store.get_all()
    return JSONResponse([record.model_dump() for record in records], status_code=200)


async def get_one_record(request: Request):
    record_id = request.path_params["record_id"]
    record = store.get_by_id(record_id)
    if record:
        return JSONResponse(record.model_dump(), status_code=200)
    else:
        return JSONResponse({"error": "Record not found"}, status_code=404)


async def create_record(request: Request):
    try:
        data = await request.json()
        record_data = RecordCreate(**data)
        new_record = store.create(record_data)
        return JSONResponse(new_record.model_dump(), status_code=201)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)


async def replace_record(request: Request):
    record_id = request.path_params["record_id"]
    try:
        if not store.get_by_id(record_id):
            return JSONResponse({"error": "Record not found"}, status_code=404)

        data = await request.json()
        record_data = RecordCreate(**data)
        store.delete(record_id)
        record = {"id": record_id, **record_data.model_dump()}
        store.records[record_id] = record
        return JSONResponse(RecordResponse(**record).model_dump(), status_code=200)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)


async def update_record(request: Request):
    record_id = request.path_params["record_id"]
    try:
        data = await request.json()
        record_data = RecordUpdate(**data)
        updated_record = store.update(record_id, record_data)
        if updated_record:
            return JSONResponse(updated_record.model_dump(), status_code=200)
        else:
            return JSONResponse({"error": "Record not found"}, status_code=404)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)


async def delete_record(request: Request):
    record_id = request.path_params["record_id"]
    if store.delete(record_id):
        return JSONResponse(None, status_code=204)
    else:
        return JSONResponse({"error": "Record not found"}, status_code=404)


routes = [
    Route("/records", get_all_records, methods=["GET"]),
    Route("/records/{record_id}", get_one_record, methods=["GET"]),
    Route("/records", create_record, methods=["POST"]),
    Route("/records/{record_id}", replace_record, methods=["PUT"]),
    Route("/records/{record_id}", update_record, methods=["PATCH"]),
    Route("/records/{record_id}", delete_record, methods=["DELETE"]),
]

app = Starlette(routes=routes)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
