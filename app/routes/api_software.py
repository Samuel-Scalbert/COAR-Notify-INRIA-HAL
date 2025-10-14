import logging
from app.app import app
from flask import request, jsonify
from app.utils.db import get_db
from app.utils.notification_handler import send_notifications_to_hal, send_notifications_to_sh, ProviderType, detect_provider_from_filename
from app.auth import require_api_key

logger = logging.getLogger(__name__)

@app.route('/api/software/status', methods=['GET'])
def software_status():
    try:
        db_manager = get_db()
        total_count = db_manager.get_collection_count("software")
        status_info = {
            "collection_name": "software",
            "total_documents": total_count,
        }
        return jsonify(status_info)
    except Exception as e:
        logger.error(f"Failed to get software status: {e}")
        return jsonify({"error": "Failed to retrieve software status"}), 500

@app.route('/api/software/<id_software>', methods=['GET'])
def software_from_id(id_software):
    try:
        db_manager = get_db()
        result = db_manager.get_software_by_normalized_name(id_software)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Failed to get software by ID {id_software}: {e}")
        return jsonify({"error": "Failed to retrieve software"}), 500

@app.route('/api/software_mention/<id_mention>', methods=['GET'])
def software_mention_from_id(id_mention):
    try:
        db_manager = get_db()
        doc = db_manager.get_document_by_key("software", id_mention)
        if doc:
            return jsonify(doc)
        else:
            return jsonify({"error": "Document not found"}), 404
    except Exception as e:
        logger.error(f"Failed to get software mention {id_mention}: {e}")
        return jsonify({"error": "Failed to retrieve software mention"}), 500

@app.route("/api/software", methods=["POST"])
@require_api_key
def insert_new_file():
    """
    Expects a JSON file uploaded as form-data with key 'file'.
    Returns meaningful HTTP status codes.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    try:
        db_manager = get_db()
        inserted = db_manager.insert_json_file(file)  # returns True if inserted, False if duplicate
    except Exception as e:
        logger.error(f"File insertion failed: {e}")
        return jsonify({"error": f"Insertion failed: {str(e)}"}), 500

    if inserted:
        try:
            send_notifications_to_hal(file)
        except Exception as e:
            logger.error(f"Notification failed: {e}")
        return jsonify({"status": "inserted", "file": file.filename}), 201
    else:
        # Still send notifications even if file already exists
        try:
            send_notifications_to_sh(file)
        except Exception as e:
            logger.error(f"Notification failed: {e}")
        return jsonify({"status": "already_exists", "file": file.filename}), 409


@app.route('/api/software/provider/<filename>', methods=['GET'])
def detect_provider(filename):
    """
    Detect the provider type from a filename.

    Args:
        filename: The filename to analyze

    Returns:
        JSON with provider information
    """
    try:
        provider = detect_provider_from_filename(filename)
        return jsonify({
            "filename": filename,
            "provider": provider.value,
            "provider_display": provider.value.replace('_', ' ').title()
        })
    except Exception as e:
        logger.error(f"Failed to detect provider for {filename}: {e}")
        return jsonify({"error": "Failed to detect provider"}), 500


@app.route('/api/software/providers', methods=['GET'])
def list_supported_providers():
    """
    List all supported providers and their capabilities.

    Returns:
        JSON with provider information
    """
    try:
        providers = []
        for provider in ProviderType:
            if provider != ProviderType.UNKNOWN:
                providers.append({
                    "name": provider.value,
                    "display_name": provider.value.replace('_', ' ').title(),
                    "patterns": {
                        ProviderType.HAL: ["hal-", "oai:hal:", ".hal."],
                        ProviderType.SOFTWARE_HERITAGE: ["swh-", "softwareheritage", ".swh."],
                        ProviderType.ZENODO: ["zenodo-", ".zenodo."],
                        ProviderType.GITHUB: ["github-", ".github."]
                    }.get(provider, [])
                })

        return jsonify({
            "supported_providers": providers,
            "total_count": len(providers)
        })
    except Exception as e:
        logger.error(f"Failed to list providers: {e}")
        return jsonify({"error": "Failed to list providers"}), 500