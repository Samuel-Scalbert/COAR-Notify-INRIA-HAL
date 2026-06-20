import logging

logger = logging.getLogger(__name__)


class Filter:
    """
    Base class for filters that *flag* mentions and documents.

    A filter never deletes or drops data. It decides whether an item should be
    flagged so that downstream consumers (notably notification sending) can
    exclude it while the underlying record is still stored and queryable.
    """

    def filter_mention(self, mention: dict) -> bool:
        """
        Return True if the mention should be flagged (excluded from notifications).

        Args:
            mention: A software mention, either in raw ingest form
                (key ``software-name``) or stored form (key ``software_name``).
        """
        raise NotImplementedError

    def filter_document(self, document: dict) -> bool:
        """
        Return True if the document should be flagged.

        Stub for now: no documents are flagged yet. Kept as an explicit
        extension point so document-level filtering can be added without
        changing the filter contract.
        """
        return False


class BlacklistFilter(Filter):
    """Flags mentions whose normalized software name is in the blacklist."""

    def __init__(self, blacklist: set[str]):
        self._blacklist = blacklist

    def filter_mention(self, mention: dict) -> bool:
        name = (mention.get("software-name") or mention.get("software_name") or {}).get(
            "normalizedForm"
        )
        return name in self._blacklist
