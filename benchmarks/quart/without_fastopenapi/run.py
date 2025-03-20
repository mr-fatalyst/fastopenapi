from quart import Quart, jsonify, request

from benchmarks.quart.without_fastopenapi.schemas import (
    RecordCreate,
    RecordResponse,
    RecordUpdate,
)
from benchmarks.quart.without_fastopenapi.storage import RecordStore

app = Quart(__name__)
store = RecordStore()


@app.route("/records", methods=["GET"])
async def get_all_records():
    records = store.get_all()
    return jsonify([record.model_dump() for record in records]), 200


@app.route("/records/<record_id>", methods=["GET"])
async def get_one_record(record_id):
    record = store.get_by_id(record_id)
    if record:
        return jsonify(record.model_dump()), 200
    else:
        return jsonify({"error": "Record not found"}), 404


@app.route("/records", methods=["POST"])
async def create_record():
    try:
        data = await request.get_json()
        record_data = RecordCreate(**data)
        new_record = store.create(record_data)
        return jsonify(new_record.model_dump()), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/records/<record_id>", methods=["PUT"])
async def replace_record(record_id):
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
    try:
        data = await request.get_json()
        record_data = RecordUpdate(**data)
        updated_record = store.update(record_id, record_data)
        if updated_record:
            return jsonify(updated_record.model_dump()), 200
        else:
            return jsonify({"error": "Record not found"}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/records/<record_id>", methods=["DELETE"])
async def delete_record(record_id):
    if store.delete(record_id):
        return "", 204
    else:
        return jsonify({"error": "Record not found"}), 404


if __name__ == "__main__":
    app.run(port=8000)
