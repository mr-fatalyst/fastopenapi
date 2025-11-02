import logging

from quart import Quart, jsonify, request

from benchmarks.common.schemas import (
    RecordCreate,
    RecordResponse,
    RecordUpdate,
)
from benchmarks.common.storage import RecordStore

app = Quart(__name__)
store = RecordStore()

logging.getLogger("quart.app").disabled = True
logging.getLogger("quart.serving").disabled = True
logging.getLogger("hypercorn.error").disabled = True
logging.getLogger("hypercorn.access").disabled = True


@app.route("/records", methods=["GET"])
async def get_all_records():
    """Get all records with response validation"""
    records = store.get_all()
    records = [RecordResponse(**r) for r in records]
    return jsonify([record.model_dump() for record in records]), 200


@app.route("/records/<record_id>", methods=["GET"])
async def get_one_record(record_id):
    """Get one record with response validation"""
    record = store.get_by_id(record_id)
    if not record:
        return jsonify({"error": "Record not found"}), 404
    record = RecordResponse(**record)
    return jsonify(record.model_dump()), 200


@app.route("/records", methods=["POST"])
async def create_record():
    """Create record with input validation"""
    try:
        data = await request.get_json()
        record_data = RecordCreate(**data)
        new_record = store.create(record_data.model_dump())
        return jsonify(new_record), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/records/<record_id>", methods=["PUT"])
async def replace_record(record_id):
    """Replace record with input and output validation"""
    try:
        if not store.get_by_id(record_id):
            return jsonify({"error": "Record not found"}), 404

        data = await request.get_json()
        record_data = RecordCreate(**data)
        store.delete(record_id)
        record = {"id": record_id, **record_data.model_dump()}
        store.records[record_id] = record
        return jsonify(RecordResponse(**record).model_dump()), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/records/<record_id>", methods=["PATCH"])
async def update_record(record_id):
    """Update record partially with input validation"""
    try:
        data = await request.get_json()
        record_data = RecordUpdate(**data)
        updated_record = store.update(
            record_id, record_data.model_dump(exclude_unset=True)
        )
        if updated_record:
            return jsonify(updated_record), 200
        else:
            return jsonify({"error": "Record not found"}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/records/<record_id>", methods=["DELETE"])
async def delete_record(record_id):
    """Delete record by ID"""
    if store.delete(record_id):
        return "", 204
    else:
        return jsonify({"error": "Record not found"}), 404


@app.route("/__reset", methods=["POST"])
async def reset_store():
    """Reset store for benchmarking"""
    store.clear()
    return "", 204


if __name__ == "__main__":
    app.run(port=8001)
