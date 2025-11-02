import uvicorn
from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from benchmarks.common import RecordCreate, RecordResponse, RecordStore, RecordUpdate

store = RecordStore()


async def get_all_records(request):
    """Get all records with response validation"""
    records = store.get_all()
    records = [RecordResponse(**r) for r in records]
    return JSONResponse([record.model_dump() for record in records])


async def get_one_record(request):
    """Get one record with response validation"""
    record_id = request.path_params["record_id"]
    record = store.get_by_id(record_id)
    if not record:
        return JSONResponse({"error": "Record not found"}, status_code=404)
    record = RecordResponse(**record)
    return JSONResponse(record.model_dump())


async def create_record(request):
    """Create record with input validation"""
    try:
        data = await request.json()
        record_data = RecordCreate(**data)
        new_record = store.create(record_data.model_dump())
        return JSONResponse(new_record, status_code=201)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)


async def replace_record(request):
    """Replace record with input and output validation"""
    record_id = request.path_params["record_id"]
    if not store.get_by_id(record_id):
        return JSONResponse({"error": "Record not found"}, status_code=404)
    try:
        data = await request.json()
        record_data = RecordCreate(**data)
        store.delete(record_id)
        record = {"id": record_id, **record_data.model_dump()}
        store.records[record_id] = record
        return JSONResponse(RecordResponse(**record).model_dump())
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)


async def update_record(request):
    """Update record partially with input validation"""
    record_id = request.path_params["record_id"]
    try:
        data = await request.json()
        record_data = RecordUpdate(**data)
        updated_record = store.update(
            record_id, record_data.model_dump(exclude_unset=True)
        )
        if updated_record:
            return JSONResponse(updated_record)
        else:
            return JSONResponse({"error": "Record not found"}, status_code=404)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)


async def delete_record(request):
    """Delete record by ID"""
    record_id = request.path_params["record_id"]
    if store.delete(record_id):
        return Response(status_code=204)
    else:
        return JSONResponse({"error": "Record not found"}, status_code=404)


async def reset_store(request):
    """Reset store for benchmarking"""
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
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="error")
