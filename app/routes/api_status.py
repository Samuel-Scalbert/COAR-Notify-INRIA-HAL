# app/routes/db_updater_json.py
from flask import jsonify
from app.app import app
from app.auth import require_api_key

@app.route("/status", methods=["GET"])
@require_api_key
def can_upload():
    
    from app.app import db

    """
    Simple route to check if the API key is valid
    and if the database is reachable.
    """
    try:
        # Check if main collections exist
        collections = ["documents", "software", "edge_doc_to_software"]
        existing = {c: db.hasCollection(c) for c in collections}

        return jsonify({
            "status": "ok",
            "can_upload": True,
            "collections": existing
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "can_upload": False
        }), 500
