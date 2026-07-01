# Mention Quality Filter

[← Back to README](../README.md)

The upstream extractor emits a large amount of junk alongside real software names: punctuation runs
(`**** ****`), repeated-token tables (`d d d d`, `SM SM SM`), sentence fragments, and entity lists. The
blacklist (exact-match) can't catch this open-ended garbage, so the optional **Mention Quality Filter** scores
every mention name as good/junk with a trained model.

- **Model**: character n-gram TF-IDF + logistic regression (`scikit-learn`). Short-string, language-agnostic,
  ~0.4 ms/mention. On held-out data: macro-F1 ≈ 0.84 (per-class F1: valid 0.91, invalid 0.77), ROC-AUC ≈ 0.93
  — reported as macro/per-class F1 rather than accuracy because the classes are imbalanced. Shipped at
  `app/static/data/name_classifier.joblib`.
  For the full dataset/training/validation methodology, metrics, and throughput, see
  [Mention Quality Filter — Model Training & Validation](validity-classifier.md).
- **Two stages, like the blacklist** — flag at ingestion, enforce at send:
  - **Ingestion**: each mention is scored and stamped with `quality_score` (P(valid), 0–1) and
    `quality_invalid` (`true` when `quality_score < MENTION_QUALITY_FILTER_THRESHOLD`). No mention is dropped.
  - **Notifications**: mentions flagged `quality_invalid` are excluded from what is sent to HAL/SWH.
- **Fully toggleable** via `MENTION_QUALITY_FILTER_ENABLED` (default `false`). The flag gates both stages: when off, the
  model is never loaded, no scoring happens, and any previously stored `quality_invalid` flags are ignored at
  send time — so enabling/disabling is reversible without re-ingesting. `MENTION_QUALITY_FILTER_THRESHOLD` (default
  `0.4`, F1-optimal) tunes how aggressive the filter is (higher = cleaner output, but drops more borderline real names).
- **Graceful degradation**: if the model file is missing or fails to load, a warning is logged once and no
  mention is flagged — ingestion never breaks.

```bash
# Enable the Mention Quality Filter; drop mentions scoring below 0.6 as P(valid)
MENTION_QUALITY_FILTER_ENABLED=true
MENTION_QUALITY_FILTER_THRESHOLD=0.6
```

- **Management & backfill**: the `/mention-quality` web UI (linked from the dashboard) shows the current
  scored / flagged counts and re-runs the filter over all stored mentions — use it to backfill mentions
  ingested before the filter existed, or after retraining. Backed by `GET /api/mention-quality/stats` and
  `POST /api/mention-quality/reapply` (see [Mention Quality Filter API](api.md#mention-quality-filter-api)). To
  review *which* mentions were flagged, use `GET /api/software/latest?quality_invalid=true`.

## Retraining / scoring (offline)

The model and its labeled dataset are produced by scripts under `sandbox/`:

| File | Purpose |
|------|---------|
| `sandbox/training_data.csv` | Labeled dataset (`name,label,source`) used to train the model |
| `sandbox/train_classifier.py` | Train, evaluate (held-out metrics + operating-point table), and save the model |
| `sandbox/score_mentions.py` | Score a full mentions CSV and report throughput |

```bash
# Retrain from sandbox/training_data.csv -> sandbox/name_classifier.joblib
python sandbox/train_classifier.py

# Try the saved model on individual names
python sandbox/train_classifier.py --predict "ImageJ" "**** ***" "DESeq2 R"

# Score an entire mentions CSV (adds SCORE + VALID columns)
python sandbox/score_mentions.py --input path/to/DOC_SOFTWARE_MENTIONS.csv
```

After retraining, copy the new `sandbox/name_classifier.joblib` to `app/static/data/name_classifier.joblib`
to ship it with the app. Re-running training over an updated `training_data.csv` is how you improve the model.
