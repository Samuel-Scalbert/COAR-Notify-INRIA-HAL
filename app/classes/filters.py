import logging
import os
from functools import lru_cache

logger = logging.getLogger(__name__)

# Trained char-ngram validity model (see sandbox/train_classifier.py). Stored next
# to the blacklist seed so it ships with the app.
_MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "static", "data", "name_classifier.joblib"
)


@lru_cache(maxsize=2)
def _load_model(path: str):
    """Load and cache the joblib pipeline once per process (keyed by absolute path).

    The model is a self-generated, trusted local artifact — not loaded from any
    untrusted source.
    """
    import joblib

    return joblib.load(path)


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


class ClassifierFilter(Filter):
    """
    Flags mentions whose name the trained classifier scores as invalid.

    Complements ``BlacklistFilter`` (exact-match on known junk): this scores the
    *structure* of any name with a char n-gram model, catching open-ended garbage
    the blacklist can never enumerate. The model is loaded once per process and
    cached. If the model file is missing it degrades gracefully — nothing is
    flagged and a warning is logged once, so ingestion never breaks.
    """

    def __init__(self, threshold: float = 0.4, model_path: str = _MODEL_PATH):
        self.threshold = threshold
        self._model_path = os.path.abspath(model_path)
        self._unavailable = False

    def _pipeline(self):
        if self._unavailable:
            return None
        try:
            return _load_model(self._model_path)
        except Exception as e:  # missing file, version mismatch, etc.
            self._unavailable = True
            logger.warning(
                f"ClassifierFilter: model unavailable at {self._model_path} ({e}); "
                "not flagging any mentions."
            )
            return None

    @staticmethod
    def _name(mention: dict) -> str | None:
        return (mention.get("software-name") or mention.get("software_name") or {}).get(
            "normalizedForm"
        )

    def score(self, mention: dict) -> float | None:
        """Return P(valid) in [0, 1], or None if the name is empty/model unavailable."""
        pipe = self._pipeline()
        name = self._name(mention)
        if pipe is None or not name:
            return None
        return float(pipe.predict_proba([name])[0, 1])

    def filter_mention(self, mention: dict) -> bool:
        """True if the model judges the mention invalid (score below threshold)."""
        s = self.score(mention)
        if s is None:
            return False  # cannot judge -> never flag
        return s < self.threshold
