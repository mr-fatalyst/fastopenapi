import logging

from quart import Quart, jsonify, request

from benchmarks.common.storage import RecordStore

app = Quart(__name__)
store = RecordStore()

logging.getLogger("quart.app").disabled = True
logging.getLogger("quart.serving").disabled = True
logging.getLogger("hypercorn.error").disabled = True
logging.getLogger("hypercorn.access").disabled = True


@app.route("/records", methods=["GET"])
async def get_all_records():
    records = store.get_all()
    return jsonify(records), 200


@app.route("/records/<record_id>", methods=["GET"])
async def get_one_record(record_id):
    record = store.get_by_id(record_id)
    if record:
        return jsonify(record), 200
    else:
        return jsonify({"error": "Record not found"}), 404


@app.route("/records", methods=["POST"])
async def create_record():
    try:
        data = await request.get_json()
        new_record = store.create(data)
        return jsonify(new_record), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/records/<record_id>", methods=["PUT"])
async def replace_record(record_id):
    try:
        if not store.get_by_id(record_id):
            return jsonify({"error": "Record not found"}), 404

        data = await request.get_json()
        store.delete(record_id)
        record = {"id": record_id, **data}
        store.records[record_id] = record
        return jsonify(record), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/records/<record_id>", methods=["PATCH"])
async def update_record(record_id):
    try:
        data = await request.get_json()
        updated_record = store.update(record_id, data)
        if updated_record:
            return jsonify(updated_record), 200
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


@app.route("/__reset", methods=["POST"])
async def reset_store():
    store.clear()
    return None


if __name__ == "__main__":
    app.run(port=8000)
