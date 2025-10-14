from app.app import app
from flask import jsonify
from app.auth import require_api_admin_key

@app.route('/api/softwares/status', methods=['GET'])
@require_api_admin_key
def software_status():
    from app.app import db  # lazy import to avoid circular import
    software_col = db["softwares"]
    total_count = software_col.count()
    status_info = {
        "collection_name": "software",
        "total_documents": total_count,
    }
    return jsonify(status_info)

@app.route('/api/softwares/<id_software>', methods=['GET'])
@require_api_admin_key
def software_from_id(id_software):
    from app.app import db
    query = f"""
        let soft_name = document("softwares/{id_software}")

        FOR soft in softwares
            filter soft.software_name.normalizedForm == soft_name.software_name.normalizedForm
            return soft
        """
    result = db.AQLQuery(query, rawResults=True)
    return jsonify(result[0:])

@app.route('/api/softwares_mention/<id_mention>', methods=['GET'])
@require_api_admin_key
def software_mention_from_id(id_mention):
    from app.app import db
    software_col = db["softwares"]
    try:
        doc = software_col.fetchDocument(id_mention)  # fetch by _key
        return jsonify(doc.getStore())  # convert to dict
    except Exception:
        return jsonify({"error": "Document not found"}), 404