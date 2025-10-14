from app.app import app
from flask import jsonify
from app.auth import require_api_admin_key

@app.route('/api/documents/status', methods=['GET'])
@require_api_admin_key
def documents_status():
    from app.app import db
    document_col = db["documents"]
    total_count = document_col.count()
    status_info = {
        "collection_name": "document",
        "total_documents": total_count,
    }
    return jsonify(status_info)

@app.route('/api/documents/<id>', methods=['GET'])
@require_api_admin_key
def document_from_id(id):
    from app.app import db
    document_col = db["documents"]
    try:
        doc = document_col.fetchDocument(id)  # fetch by _key
        return jsonify(doc.getStore())  # convert to dict
    except Exception:
        return jsonify({"error": "Document not found"}), 404

@app.route('/api/documents/<id_document>/softwares', methods=['GET'])
@require_api_admin_key
def document_softwares_all_from_id(id_document):
    from app.app import db
    query = f"""
    FOR edge IN edge_doc_to_software
    FILTER edge._from == "documents/{id_document}"
    let soft = document(edge._to)
    return soft
    """
    result = db.AQLQuery(query, rawResults=True)
    return jsonify(result[0:])

@app.route('/api/documents/<id_document>/softwares/<id_software>', methods=['GET'])
@require_api_admin_key
def document_softwares_from_id(id_document, id_software):
    from app.app import db
    query = f"""
    let soft_name = document("softwares/{id_software}")

    FOR edge IN edge_doc_to_software
        FILTER edge._from == "documents/{id_document}"
        let soft = document(edge._to)
        filter soft.software_name.normalizedForm == soft_name.software_name.normalizedForm
        return soft
    """
    result = db.AQLQuery(query, rawResults=True)
    return jsonify(result[0:])