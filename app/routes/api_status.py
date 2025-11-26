import logging
from flask import jsonify
from app.app import app
from app.utils.db import get_db
from app.auth import require_api_key

logger = logging.getLogger(__name__)

@app.route("/status", methods=["GET"])
@require_api_key
def can_upload():
    """
    Simple route to check if the API key is valid
    and if the database is reachable.
    """
    try:
        db_manager = get_db()

        # Check if main collections exist
        collections = ["documents", "software", "edge_doc_to_software"]
        existing = {}

        for collection in collections:
            try:
                collection_obj = db_manager.get_collection(collection)
                existing[collection] = collection_obj is not None
            except Exception as e:
                logger.warning(f"Failed to check collection {collection}: {e}")
                existing[collection] = False

        # If any essential collection is missing, we can't upload
        can_upload = all(existing.values())

        return jsonify({
            "status": "ok" if can_upload else "error",
            "can_upload": can_upload,
            "collections": existing
        })

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "can_upload": False
        }), 500
