import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response

from benchmarks.common import RecordCreate, RecordResponse, RecordStore, RecordUpdate

app = FastAPI(
    title="Record API",
    description="A simple Record API built with FastAPI",
    version="1.0.0",
)

store = RecordStore()


@app.get("/records", response_model=list[RecordResponse], tags=["records"])
async def get_all_records():
    """Get all records"""
    return store.get_all()


@app.get("/records/{record_id}", response_model=RecordResponse, tags=["records"])
async def get_one_record(record_id: str):
    """Get a specific record by ID"""
    record = store.get_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@app.post("/records", response_model=RecordResponse, status_code=201, tags=["records"])
async def create_record(record: RecordCreate):
    """Create a new record"""
    return store.create(record.model_dump())


@app.put("/records/{record_id}", response_model=RecordResponse, tags=["records"])
async def replace_record(record_id: str, record: RecordCreate):
    """Update a record completely (all fields required)"""
    existing_record = store.get_by_id(record_id)
    if not existing_record:
        raise HTTPException(status_code=404, detail="Record not found")

    store.delete(record_id)
    new_record = {"id": record_id, **record.model_dump()}
    store.records[record_id] = new_record
    return new_record


@app.patch("/records/{record_id}", response_model=RecordResponse, tags=["records"])
async def update_record(record_id: str, record: RecordUpdate):
    """Update a record partially (only specified fields)"""
    updated_record = store.update(record_id, record.model_dump(exclude_unset=True))
    if not updated_record:
        raise HTTPException(status_code=404, detail="Record not found")
    return updated_record


@app.delete("/records/{record_id}", status_code=204, tags=["records"])
async def delete_record(record_id: str):
    """Delete a record"""
    if not store.delete(record_id):
        raise HTTPException(status_code=404, detail="Record not found")
    return Response(status_code=204)


@app.post("/__reset", status_code=204)
def reset_store():
    store.clear()


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8003, log_level="error")
