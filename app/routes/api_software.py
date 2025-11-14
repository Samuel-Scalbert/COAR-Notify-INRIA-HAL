import logging
from app.app import app
from flask import request, jsonify
from app.utils.db import get_db
from app.utils.blacklist_manager import blacklist_manager
from app.auth import require_api_key

logger = logging.getLogger(__name__)

@app.route('/api/software', methods=['GET'])
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

@app.route('/api/software/name/<name>', methods=['GET'])
def software_from_id(name):
    try:
        db_manager = get_db()
        result = db_manager.get_software_by_normalized_name(name)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Failed to get software by {name}: {e}")
        return jsonify({"error": "Failed to retrieve software"}), 500

@app.route('/api/software/<id_mention>', methods=['GET'])
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


# Blacklist management endpoints
@app.route('/api/blacklist', methods=['GET'])
def get_blacklist():
    """
    Get the current blacklist of software terms.

    Query Parameters:
    - search: Search terms (optional)
    - limit: Maximum number of results (default: 50)

    Returns:
        JSON with blacklist data
    """
    try:
        search_query = request.args.get('search', '').strip()
        limit = int(request.args.get('limit', 50))

        stats = blacklist_manager.get_blacklist_stats()

        if search_query:
            terms = blacklist_manager.search_blacklist(search_query, limit)
            return jsonify({
                "stats": stats,
                "terms": terms,
                "search_query": search_query,
                "limit": limit,
                "total_matches": len(terms)
            })
        else:
            # Return all terms if no search
            all_terms = sorted(blacklist_manager.get_blacklist())
            return jsonify({
                "stats": stats,
                "terms": all_terms,
                "total_count": len(all_terms)
            })
    except Exception as e:
        logger.error(f"Failed to get blacklist: {e}")
        return jsonify({"error": "Failed to retrieve blacklist"}), 500


@app.route('/api/blacklist/stats', methods=['GET'])
def get_blacklist_stats():
    """
    Get statistics about the blacklist.

    Returns:
        JSON with blacklist statistics
    """
    try:
        stats = blacklist_manager.get_blacklist_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Failed to get blacklist stats: {e}")
        return jsonify({"error": "Failed to retrieve blacklist statistics"}), 500


@app.route('/api/blacklist', methods=['POST'])
@require_api_key
def add_to_blacklist():
    """
    Add a term to the blacklist.

    JSON Body:
    - term: term to add to blacklist (required)

    Returns:
        JSON with operation result
    """
    try:
        data = request.get_json()
        if not data or 'term' not in data:
            return jsonify({"error": "term is required in request body"}), 400

        term = data['term'].strip()
        if not term:
            return jsonify({"error": "term cannot be empty"}), 400

        if blacklist_manager.add_to_blacklist(term):
            return jsonify({
                "success": True,
                "message": f"Term '{term}' added to blacklist",
                "term": term
            }), 201
        else:
            return jsonify({
                "success": False,
                "message": f"Term '{term}' already exists in blacklist",
                "term": term
            }), 409
    except Exception as e:
        logger.error(f"Failed to add term to blacklist: {e}")
        return jsonify({"error": "Failed to add term to blacklist"}), 500


@app.route('/api/blacklist/<term>', methods=['DELETE'])
@require_api_key
def remove_from_blacklist(term):
    """
    Remove a term from the blacklist.

    Args:
        term: term to remove from blacklist

    Returns:
        JSON with operation result
    """
    try:
        if blacklist_manager.remove_from_blacklist(term):
            return jsonify({
                "success": True,
                "message": f"Term '{term}' removed from blacklist",
                "term": term
            })
        else:
            return jsonify({
                "success": False,
                "message": f"Term '{term}' not found in blacklist",
                "term": term
            }), 404
    except Exception as e:
        logger.error(f"Failed to remove term from blacklist: {e}")
        return jsonify({"error": "Failed to remove term from blacklist"}), 500


@app.route('/api/blacklist/reload', methods=['POST'])
@require_api_key
def reload_blacklist():
    """
    Reload the blacklist from file.

    Returns:
        JSON with reload result
    """
    try:
        term_count = blacklist_manager.reload_blacklist()
        return jsonify({
            "success": True,
            "message": f"Blacklist reloaded successfully",
            "total_terms": term_count
        })
    except Exception as e:
        logger.error(f"Failed to reload blacklist: {e}")
        return jsonify({"error": "Failed to reload blacklist"}), 500


@app.route('/api/blacklist/export', methods=['GET'])
def export_blacklist():
    """
    Export the blacklist as CSV.

    Returns:
        CSV file download
    """
    try:
        csv_content = blacklist_manager.export_blacklist()

        from flask import Response
        response = Response(
            csv_content,
            mimetype='text/csv',
            headers={
                'Content-Disposition': 'attachment; filename=blacklist.csv'
            }
        )
        return response
    except Exception as e:
        logger.error(f"Failed to export blacklist: {e}")
        return jsonify({"error": "Failed to export blacklist"}), 500


@app.route('/api/blacklist/import', methods=['POST'])
@require_api_key
def import_blacklist():
    """
    Import blacklist from CSV file upload.

    Form Data:
    - file: CSV file to import (required)
    - overwrite: Whether to overwrite existing blacklist (default: false)

    Returns:
        JSON with import result
    """
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']
        if not file.filename.endswith('.csv'):
            return jsonify({"error": "File must be a CSV file"}), 400

        overwrite = request.form.get('overwrite', 'false').lower() in ['true', '1', 'yes']

        csv_content = file.read().decode('utf-8')
        result = blacklist_manager.import_blacklist_from_csv(csv_content, overwrite)

        if result['success']:
            return jsonify({
                "success": True,
                "message": f"Successfully imported {result['imported_terms']} terms",
                "total_terms": result['total_terms'],
                "overwrite": result['overwrite']
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get('error', 'Import failed')
            }), 400

    except Exception as e:
        logger.error(f"Failed to import blacklist: {e}")
        return jsonify({"error": "Failed to import blacklist"}), 500