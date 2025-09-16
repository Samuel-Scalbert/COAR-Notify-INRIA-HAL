from app.app import app
from flask import jsonify

@app.route('/api/documents/status', methods=['GET'])
def document_status():
    from app.app import db
    document_col = db["documents"]
    total_count = document_col.count()
    status_info = {
        "collection_name": "document",
        "total_documents": total_count,
    }
    return jsonify(status_info)
