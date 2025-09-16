from app.app import app
from flask import jsonify

@app.route('/api/softwares/status', methods=['GET'])
def software_status():
    from app.app import db  # lazy import to avoid circular import
    software_col = db["softwares"]
    total_count = software_col.count()
    status_info = {
        "collection_name": "software",
        "total_documents": total_count,
    }
    return jsonify(status_info)
