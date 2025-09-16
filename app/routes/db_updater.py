from flask import request, jsonify
from app.app import app  # only import app
from app.utils.db import insert_json_file
from app.auth import require_api_key

@app.route("/insert", methods=["POST"])
@require_api_key
def insert_new_file():
    """
    Expects a JSON file uploaded as form-data with key 'file'.
    Returns meaningful HTTP status codes.
    """
    from app.app import db  # import db locally to avoid circular import

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    try:
        inserted = insert_json_file(file, db)  # returns True if inserted, False if duplicate
        if inserted:
            return jsonify({"status": "inserted", "file": file.filename}), 201
        else:
            return jsonify({"status": "already_exists", "file": file.filename}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500
