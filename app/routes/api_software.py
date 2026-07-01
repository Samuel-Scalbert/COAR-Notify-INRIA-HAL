import logging

from flask import Blueprint, Response, jsonify, request

from app.utils.blacklist_manager import blacklist_manager
from app.utils.db import get_db

logger = logging.getLogger(__name__)

api_software_bp = Blueprint("api_software", __name__)


@api_software_bp.route("/api/software", methods=["GET"])
def software_status():
    try:
        db_manager = get_db()
        total_count = db_manager.get_collection_count("software")
        return jsonify(
            {
                "collection_name": "software",
                "total_documents": total_count,
            }
        )
    except Exception as e:
        logger.error(f"Failed to get software status: {e}")
        return jsonify({"error": "Failed to retrieve software status"}), 500


def _parse_bool_arg(name: str) -> bool | None:
    """Parse an optional tri-state boolean query param.

    Returns None when the param is absent or unrecognized (so the filter is
    skipped), True for true/1/yes/on, False for false/0/no/off.
    """
    raw = request.args.get(name)
    if raw is None:
        return None
    v = raw.strip().lower()
    if v in ("true", "1", "yes", "on"):
        return True
    if v in ("false", "0", "no", "off"):
        return False
    return None


@api_software_bp.route("/api/software/latest", methods=["GET"])
def latest_software():
    """
    Return the most recently ingested software mentions, newest first.

    Each mention includes the ``blacklisted`` / ``quality_invalid`` flags, the
    ``quality_score`` (P(valid), or null when not scored), and a ``context``
    object with the created/used/shared characterization booleans.

    Query params:
      - ``limit`` (1-100, default 10): how many to return.
      - ``blacklisted`` (true/false): keep only blacklisted / non-blacklisted mentions.
      - ``quality_invalid`` (true/false): keep only quality-invalid / quality-valid mentions.

    Public (no API key) so it can be linked directly from the dashboard. This
    static rule is matched ahead of ``/api/software/<id_mention>`` by Werkzeug,
    so "latest" is never treated as a mention id.
    """
    limit = request.args.get("limit", default=10, type=int) or 10
    limit = max(1, min(limit, 100))
    blacklisted = _parse_bool_arg("blacklisted")
    quality_invalid = _parse_bool_arg("quality_invalid")
    try:
        mentions = get_db().get_latest_mentions(
            limit=limit, blacklisted=blacklisted, quality_invalid=quality_invalid
        )
        return jsonify(
            {
                "count": len(mentions),
                "limit": limit,
                "filters": {"blacklisted": blacklisted, "quality_invalid": quality_invalid},
                "mentions": mentions,
            }
        )
    except Exception as e:
        logger.error(f"Failed to get latest software mentions: {e}")
        return jsonify({"error": "Failed to retrieve latest software mentions"}), 500


@api_software_bp.route("/api/software/name/<name>", methods=["GET"])
def software_from_name(name):
    try:
        db_manager = get_db()
        return jsonify(db_manager.get_software_by_normalized_name(name))
    except Exception as e:
        logger.error(f"Failed to get software by {name}: {e}")
        return jsonify({"error": "Failed to retrieve software"}), 500


@api_software_bp.route("/api/software/<id_mention>", methods=["GET"])
def software_mention_from_id(id_mention):
    try:
        db_manager = get_db()
        doc = db_manager.get_document_by_key("software", id_mention)
        if doc:
            return jsonify(doc)
        return jsonify({"error": "Software mention not found"}), 404
    except Exception as e:
        logger.error(f"Failed to get software mention {id_mention}: {e}")
        return jsonify({"error": "Failed to retrieve software mention"}), 500


# Blacklist management endpoints


@api_software_bp.route("/api/blacklist", methods=["GET"])
def get_blacklist():
    try:
        search_query = request.args.get("search", "").strip()
        limit = int(request.args.get("limit", 50))

        stats = blacklist_manager.get_blacklist_stats()

        if search_query:
            terms = blacklist_manager.search_blacklist(search_query, limit)
            return jsonify(
                {
                    "stats": stats,
                    "terms": terms,
                    "search_query": search_query,
                    "limit": limit,
                    "total_matches": len(terms),
                }
            )

        all_terms = sorted(blacklist_manager.get_blacklist())
        return jsonify(
            {
                "stats": stats,
                "terms": all_terms,
                "total_count": len(all_terms),
            }
        )
    except Exception as e:
        logger.error(f"Failed to get blacklist: {e}")
        return jsonify({"error": "Failed to retrieve blacklist"}), 500


@api_software_bp.route("/api/blacklist/stats", methods=["GET"])
def get_blacklist_stats():
    try:
        return jsonify(blacklist_manager.get_blacklist_stats())
    except Exception as e:
        logger.error(f"Failed to get blacklist stats: {e}")
        return jsonify({"error": "Failed to retrieve blacklist statistics"}), 500


@api_software_bp.route("/api/blacklist/match-count", methods=["GET"])
def blacklist_match_count():
    """
    Read-only: how many stored software mentions the current blacklist would flag.

    Returns total mentions, matching mentions, distinct matching names, and the
    blacklist size. Does not modify any data (unlike reapply).
    """
    try:
        return jsonify(get_db().count_software_matching_blacklist())
    except Exception as e:
        logger.error(f"Failed to count blacklist matches: {e}")
        return jsonify({"error": "Failed to count blacklist matches"}), 500


@api_software_bp.route("/api/blacklist", methods=["POST"])
def add_to_blacklist():
    try:
        data = request.get_json()
        if not data or "term" not in data:
            return jsonify({"error": "term is required in request body"}), 400

        term = data["term"].strip()
        if not term:
            return jsonify({"error": "term cannot be empty"}), 400

        if blacklist_manager.add_to_blacklist(term):
            return jsonify(
                {
                    "success": True,
                    "message": f"Term '{term}' added to blacklist",
                    "term": term,
                }
            ), 201
        return jsonify(
            {
                "success": False,
                "message": f"Term '{term}' already exists in blacklist",
                "term": term,
            }
        ), 409
    except Exception as e:
        logger.error(f"Failed to add term to blacklist: {e}")
        return jsonify({"error": "Failed to add term to blacklist"}), 500


@api_software_bp.route("/api/blacklist/<path:term>", methods=["DELETE"])
def remove_from_blacklist(term):
    try:
        if blacklist_manager.remove_from_blacklist(term):
            return jsonify(
                {
                    "success": True,
                    "message": f"Term '{term}' removed from blacklist",
                    "term": term,
                }
            )
        return jsonify(
            {
                "success": False,
                "message": f"Term '{term}' not found in blacklist",
                "term": term,
            }
        ), 404
    except Exception as e:
        logger.error(f"Failed to remove term from blacklist: {e}")
        return jsonify({"error": "Failed to remove term from blacklist"}), 500


@api_software_bp.route("/api/blacklist/reload", methods=["POST"])
def reload_blacklist():
    try:
        term_count = blacklist_manager.reload_blacklist()
        return jsonify(
            {
                "success": True,
                "message": "Blacklist reloaded successfully",
                "total_terms": term_count,
            }
        )
    except Exception as e:
        logger.error(f"Failed to reload blacklist: {e}")
        return jsonify({"error": "Failed to reload blacklist"}), 500


@api_software_bp.route("/api/blacklist/reapply", methods=["POST"])
def reapply_blacklist():
    """
    Recompute the ``blacklisted`` flag on all already-stored software mentions
    against the current (live) blacklist. Use this to propagate blacklist edits
    to existing documents and to backfill the flag on legacy mentions.
    """
    try:
        result = get_db().reapply_blacklist(blacklist_manager.get_blacklist())
        return jsonify({"status": "reapplied", **result})
    except Exception as e:
        logger.error(f"Failed to reapply blacklist: {e}")
        return jsonify({"error": "Failed to reapply blacklist"}), 500


@api_software_bp.route("/api/mention-quality/stats", methods=["GET"])
def mention_quality_stats():
    """
    Read-only: how the Mention Quality Filter flags currently stand.

    Returns total mentions, how many have been scored, how many are flagged
    invalid, the distinct-name count, and the active threshold / enabled state.
    Does not modify any data (unlike reapply).
    """
    try:
        return jsonify(get_db().get_mention_quality_stats())
    except Exception as e:
        logger.error(f"Failed to get mention quality stats: {e}")
        return jsonify({"error": "Failed to retrieve mention quality stats"}), 500


@api_software_bp.route("/api/mention-quality/reapply", methods=["POST"])
def reapply_mention_quality():
    """
    Re-score every stored software mention with the current model and rewrite the
    ``quality_score`` / ``quality_invalid`` flags. Use this to backfill mentions
    ingested before the model existed and to propagate a retrained model.
    """
    try:
        result = get_db().reapply_mention_quality()
        return jsonify({"status": "reapplied", **result})
    except Exception as e:
        logger.error(f"Failed to reapply mention quality filter: {e}")
        return jsonify({"error": "Failed to reapply mention quality filter"}), 500


@api_software_bp.route("/api/blacklist/export", methods=["GET"])
def export_blacklist():
    try:
        csv_content = blacklist_manager.export_blacklist()
        return Response(
            csv_content,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=blacklist.csv"},
        )
    except Exception as e:
        logger.error(f"Failed to export blacklist: {e}")
        return jsonify({"error": "Failed to export blacklist"}), 500


@api_software_bp.route("/api/blacklist/import", methods=["POST"])
def import_blacklist():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        if not file.filename.endswith(".csv"):
            return jsonify({"error": "File must be a CSV file"}), 400

        overwrite = request.form.get("overwrite", "false").lower() in ["true", "1", "yes"]
        csv_content = file.read().decode("utf-8")
        result = blacklist_manager.import_blacklist_from_csv(csv_content, overwrite)

        if result["success"]:
            return jsonify(
                {
                    "success": True,
                    "message": f"Successfully imported {result['imported_terms']} terms",
                    "total_terms": result["total_terms"],
                    "overwrite": result["overwrite"],
                }
            )
        return jsonify(
            {
                "success": False,
                "error": result.get("error", "Import failed"),
            }
        ), 400
    except Exception as e:
        logger.error(f"Failed to import blacklist: {e}")
        return jsonify({"error": "Failed to import blacklist"}), 500
