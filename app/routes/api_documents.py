import logging
from app.app import app
from flask import jsonify
from app.utils.db import get_db

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