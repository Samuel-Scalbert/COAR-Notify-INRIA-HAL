from flask import request, jsonify
from app.app import app  # only import app
from app.utils.db import insert_json_file
from app.utils.notification_JSON_to_HAL import notification_JSON_to_HAL

@app.route("/insert", methods=["POST"])
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
    except Exception as e:
        return jsonify({"error": f"Insertion failed: {str(e)}"}), 500

    if inserted:
        try:
            notification_JSON_to_HAL(file)
        except Exception as e:
            print(f"Notification failed: {e}")
        return jsonify({"status": "inserted", "file": file.filename}), 201
    else:
        notification_JSON_to_HAL(file)
        return jsonify({"status": "already_exists", "file": file.filename}), 409

