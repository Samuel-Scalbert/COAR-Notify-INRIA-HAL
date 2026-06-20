import csv
import io
import logging

logger = logging.getLogger(__name__)

# Seed CSV shipped in the image; used only to populate the persistent ArangoDB
# collection the first time (and on an explicit reload). The blacklist itself
# lives in ArangoDB so runtime edits survive restarts.
_blacklist_seed_path = "./app/static/data/blacklist.csv"


class BlacklistManager:
    """
    Centralized blacklist management, backed by the ArangoDB ``blacklist`` collection.

    This is a thin facade over the database layer (DatabaseManager): all state
    lives in ArangoDB, so edits made through the API/UI persist across restarts.
    The database is resolved lazily (via ``get_db()``) because the connection is
    not ready at import time.
    """

    def __init__(self, seed_path: str = None):
        self.seed_path = seed_path or _blacklist_seed_path

    def _db(self):
        from app.utils.db import get_db

        return get_db()

    def get_blacklist(self) -> set[str]:
        """Return the current blacklist as a set of terms."""
        return self._db().get_blacklist_terms()

    def is_blacklisted(self, term: str) -> bool:
        """Check whether a term is in the blacklist."""
        return term in self._db().get_blacklist_terms()

    def add_to_blacklist(self, term: str) -> bool:
        """Add a term. Returns True if added, False if blank or already present."""
        return self._db().add_blacklist_term(term)

    def remove_from_blacklist(self, term: str) -> bool:
        """Remove a term. Returns True if removed, False if not found."""
        return self._db().remove_blacklist_term(term)

    def seed_if_empty(self) -> int:
        """Populate the collection from the seed CSV if it is empty (one-time migration)."""
        return self._db().seed_blacklist_from_csv(self.seed_path)

    def reload_blacklist(self) -> int:
        """
        Merge the seed CSV into the collection (adds any missing terms) and return
        the total term count. Existing terms are left untouched.
        """
        db = self._db()
        for term in db.load_blacklist(self.seed_path):
            db.add_blacklist_term(term)
        return db.count_blacklist_terms()

    def get_blacklist_stats(self) -> dict:
        """Return statistics about the blacklist."""
        return {
            "total_terms": self._db().count_blacklist_terms(),
            "storage": "arangodb",
            "collection": "blacklist",
            "seed_path": self.seed_path,
        }

    def search_blacklist(self, query: str, limit: int = 50) -> list[str]:
        """Case-insensitive substring search over the blacklist."""
        if not query:
            return []
        query_lower = query.lower()
        matches = [t for t in self._db().get_blacklist_terms() if query_lower in t.lower()]
        return sorted(matches)[:limit]

    def export_blacklist(self) -> str:
        """Export the blacklist as a CSV string (one term per line, with header)."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["term"])
        for term in sorted(self._db().get_blacklist_terms()):
            writer.writerow([term])
        return output.getvalue()

    def import_blacklist_from_csv(self, csv_content: str, overwrite: bool = False) -> dict:
        """
        Import terms from CSV content into the collection.

        Args:
            csv_content: CSV string content
            overwrite: If True, clear the collection before importing.

        Returns:
            Dict with import results.
        """
        try:
            db = self._db()
            reader = csv.reader(io.StringIO(csv_content))
            first_row = next(reader, None)
            if first_row and first_row[0].lower() not in ["term", "word", "pattern"]:
                # Not a header — treat the first row as data.
                reader = iter([first_row, *list(reader)])

            new_terms = {row[0].strip() for row in reader if row and row[0].strip()}

            if overwrite:
                db.clear_blacklist()

            added = sum(1 for term in new_terms if db.add_blacklist_term(term))
            return {
                "success": True,
                "imported_terms": added,
                "total_terms": db.count_blacklist_terms(),
                "overwrite": overwrite,
            }
        except Exception as e:
            logger.error(f"Failed to import blacklist: {e}")
            return {"success": False, "error": str(e)}


# Global blacklist manager instance (state lives in ArangoDB, resolved lazily).
blacklist_manager = BlacklistManager()
