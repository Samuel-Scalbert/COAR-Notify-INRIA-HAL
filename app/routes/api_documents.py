import logging
from app.app import app
from flask import jsonify, request

from app.auth import require_api_key
from app.utils.db import get_db
from app.utils.notification_handler import send_notifications_to_sh, send_notifications_to_hal

logger = logging.getLogger(__name__)

@app.route('/api/documents/status', methods=['GET'])
def documents_status():
    try:
        db_manager = get_db()
        total_count = db_manager.get_collection_count("documents")
        status_info = {
            "collection_name": "documents",
            "total_documents": total_count,
        }
        return jsonify(status_info)
    except Exception as e:
        logger.error(f"Failed to get documents status: {e}")
        return jsonify({"error": "Failed to retrieve documents status"}), 500

@app.route('/api/documents/<id>', methods=['GET'])
def document_from_id(id):
    try:
        db_manager = get_db()
        doc = db_manager.get_document_by_key("documents", id)
        if doc:
            return jsonify(doc)
        else:
            return jsonify({"error": "Document not found"}), 404
    except Exception as e:
        logger.error(f"Failed to get document {id}: {e}")
        return jsonify({"error": "Failed to retrieve document"}), 500

@app.route('/api/documents/<id_document>/software', methods=['GET'])
def document_software_all_from_id(id_document):
    try:
        db_manager = get_db()
        result = db_manager.get_document_software(id_document)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Failed to get software for document {id_document}: {e}")
        return jsonify({"error": "Failed to retrieve document software"}), 500

@app.route('/api/documents/<id_document>/software/<id_software>', methods=['GET'])
def document_software_from_id(id_document, id_software):
    try:
        db_manager = get_db()
        result = db_manager.get_document_software(id_document, id_software)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Failed to get software {id_software} for document {id_document}: {e}")
        return jsonify({"error": "Failed to retrieve document software"}), 500


@app.route("/api/document", methods=["POST"])
@require_api_key
def insert_new_document():
    """
    Expects a JSON file of a document uploaded as form-data with key 'file' and a mandatory document_id parameter.
    The document_id will be used as the HAL identifier instead of extracting from filename.

    Form-data fields:
    - file: JSON file containing software metadata (required)
    - document_id: HAL identifier for the document (required)

    Returns meaningful HTTP status codes.
    """
    # Validate required fields
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    document_id = request.form.get("document_id")
    if not document_id:
        return jsonify({"error": "document_id parameter is required"}), 400

    file = request.files["file"]

    try:
        db_manager = get_db()
        # Override the filename with the provided document_id for HAL identification
        original_filename = file.filename
        file.filename = document_id

        inserted = db_manager.insert_document_as_json(document_id, file)  # returns True if inserted, False if duplicate

        # Restore original filename for logging and notifications
        file.filename = original_filename

    except Exception as e:
        logger.error(f"File insertion failed: {e}")
        return jsonify({"error": f"Insertion failed: {str(e)}"}), 500

    if inserted:
        try:
            # Create a new file-like object with the document_id for notifications
            from werkzeug.datastructures import FileStorage
            import io

            # Read the file content
            file_content = file.read()
            file.seek(0)  # Reset file pointer

            # Create a new FileStorage object with document_id as filename for notifications
            notification_file = FileStorage(
                stream=io.BytesIO(file_content),
                filename=document_id,
                content_type=file.content_type,
                content_length=file.content_length
            )

            send_notifications_to_hal(notification_file)
        except Exception as e:
            logger.error(f"Notification failed: {e}")
        return jsonify({
            "status": "inserted",
            "file": original_filename,
            "document_id": document_id
        }), 201
    else:
        # Still send notifications even if file already exists
        try:
            from werkzeug.datastructures import FileStorage
            import io

            file_content = file.read()
            file.seek(0)

            notification_file = FileStorage(
                stream=io.BytesIO(file_content),
                filename=document_id,
                content_type=file.content_type,
                content_length=file.content_length
            )

            send_notifications_to_sh(notification_file)
        except Exception as e:
            logger.error(f"Notification failed: {e}")
        return jsonify({
            "status": "already_exists",
            "file": original_filename,
            "document_id": document_id
        }), 409