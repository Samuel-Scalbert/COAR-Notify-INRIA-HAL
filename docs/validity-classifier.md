# Software Mention Validity Classifier — Training & Validation

This page documents how the structural validity classifier (the model behind
`MODEL_FILTER_ENABLED`, see the [README](../README.md#software-mention-validity-classifier))
was built and evaluated: the labeling methodology, the model, the validation
protocol, and the measured accuracy and throughput.

> All metrics below were measured locally on the development machine (single
> process, `scikit-learn` 1.9.0, Python 3.11). Timings will vary with hardware.

---

## 1. Motivation

HAL receives a large volume of extracted "software mentions", a substantial share
of which are **not software names** but extraction artifacts: punctuation runs
(`**** ****`), repeated-token tables (`d d d d`, `SM SM SM`), sentence/phrase
fragments, entity lists, and chemical formulas. The exact-match **blacklist**
cannot enumerate this open-ended garbage, so we trained a classifier to score the
*structure* of any name and decide whether it is a plausible software name.

An initial **hand-tuned heuristic** (character-distribution rules) was prototyped
and then abandoned: it plateaued because the decision is partly *semantic*
(`mclust` is software, `Configuration` is not) and the two error directions need
opposite fixes — measured at ~44% disagreement with ground truth on a stratified
sample of the grey zone. We pivoted to a **labeled dataset + learned model**.

---

## 2. Labeling policy (clean-name)

Labels follow a **structural / clean-name** policy (not "do I recognize this
software?"):

- **valid (1)** — a clean, plausible *name*: a software / tool / library / package
  / platform / file-format name, a product or brand, or a name-like
  acronym/identifier. Minor trailing/leading noise is acceptable if the name is
  still clear (`DESeq2 R`, `MEGA X`, `R package « mclust »`).
- **invalid (0)** — not a clean name: punctuation/symbol noise, sentences/phrases
  (any language), lists of multiple entities, repeated-token/garbled tables,
  mid-word fragments, chemical formulas/solvent notation (`MeCN/DMSO`,
  `TiO 2 /SiO 2`), and generic standalone words that are not names (`SCATTERPLOT`).

The policy is deliberately **knowledge-light** so labeling is consistent and so a
character-level model can learn it.

---

## 3. Dataset construction

### Source

- Input: `DOC_SOFTWARE_MENTIONS.csv` — **51,634** mention rows, **19,889 unique**
  names (the dataset is built on unique names; duplicates inherit the label).

### Labeling pipeline

Labels were produced by a staged, multi-model pipeline and saved to
`sandbox/training_data.csv` (`name,label,source`):

1. **Heuristic auto-label** — names that are unambiguous symbol junk (high
   character-distribution junk score) were labeled `invalid` without a model
   (`source=heuristic-auto`).
2. **LLM bulk labeling (Haiku)** — the remaining ~18.6k names were labeled by a
   fan-out of **125 batched agents** (150 names/batch) under the clean-name
   policy.
3. **Verification pass (Sonnet)** — the ~4.8k *borderline* names (structurally
   name-like but model-rejected, or model-accepted but suspicious) were re-judged
   by a stronger model; disagreements overrode Haiku. This rescued **1,593**
   real-software names wrongly rejected and corrected **32** false-valids.
4. **Full uniformity sweep (Sonnet)** — the remaining 13.7k Haiku-only rows were
   re-judged by Sonnet for a single consistent labeler; this flipped **496** rows
   (118 → valid, 378 → invalid; Sonnet's blind spot on "easy" rows was *false
   positives*, the opposite of Haiku's).
5. **Human seed (authoritative)** — a 180-row stratified sample was hand-labeled
   and overrides any model label where they overlap.

**Robustness note:** the fan-out keys each label to the **absolute line number**
that the `Read` tool prints, not to position in the returned array. An earlier
position-aligned version discarded any batch whose count was off by one (LLMs
occasionally skip/merge a line), losing 85% of labels; line-keying + keeping
partial results reduced loss to **0 missing**.

### Final composition

| | count | share |
|---|---|---|
| **valid (1)** | 14,658 | 73.7% |
| **invalid (0)** | 5,231 | 26.3% |
| **total (unique)** | **19,889** | 100% |

By labeler provenance:

| source | count | confidence |
|---|---|---|
| `sonnet-verified` | 18,478 | strong model, full clean-name policy |
| `human` | 180 | hand-labeled, authoritative |
| `heuristic-auto` | 1,231 | pure-symbol junk, trivially invalid |

### Labeling cost

≈ **3.8M output tokens** of productive LLM usage (Haiku bulk ≈ 2.0M, Sonnet
verification ≈ 0.5M, Sonnet sweep ≈ 1.3M), plus one discarded run from the
batching bug noted above.

### Label quality

On the 180-row human held-out seed, the LLM pipeline agreed with human labels
**90%** of the time. Remaining disagreements are the irreducible grey zone (e.g.
`DNS`, very long descriptive full-names) where reasonable labelers differ.

---

## 4. Model

Trained by `sandbox/train_classifier.py`:

- **Features**: character n-grams via `TfidfVectorizer`
  - `analyzer="char_wb"` (word-boundary aware), `ngram_range=(2, 5)`, `min_df=2`,
    `sublinear_tf=True`, `lowercase=False` (case is signal: `ImageJ` vs `image j`).
  - Character n-grams are language-agnostic and capture both character
    distribution (garbage) and subword/morpheme patterns (real names).
- **Classifier**: `LogisticRegression(class_weight="balanced", C=4.0, max_iter=2000)`
  — `class_weight="balanced"` offsets the 74/26 class imbalance.
- **Artifact**: `app/static/data/name_classifier.joblib` (~1.4 MB), loaded once
  per process and cached.

---

## 5. Validation method

- **Hold-out**: stratified 80/20 train/test split (`random_state=42`) →
  15,911 train / 3,978 test.
- **Cross-validation**: 5-fold `f1_macro` on the training split for a stability
  estimate.
- The shipped model is **refit on all 19,889 rows** after evaluation (more data,
  better final model); the metrics below come from the held-out split.

---

## 6. Results — precision / recall / F1

The classes are imbalanced (73.7% valid / 26.3% invalid), so we report
**precision, recall and F1 per class** plus **macro-F1** as the primary metrics.
Plain accuracy is reported only as a secondary figure, with its caveat, because a
trivial "always predict valid" baseline already scores 73.7% accuracy.

**5-fold CV (train):** macro-F1 = **0.832 ± 0.011** (stable).

**Held-out test (3,978 examples, threshold 0.5):**

| class       | precision | recall | f1        | support |
|-------------|-----------|--------|-----------|---------|
| invalid     | 0.747     | 0.792  | 0.769     | 1,046   |
| valid       | 0.924     | 0.905  | 0.914     | 2,932   |
| **macro avg** | **0.836** | **0.848** | **0.841** | 3,978 |

**Primary (imbalance-robust) headline:** macro-F1 = **0.841**, ROC-AUC = **0.926**.

The `valid` class is detected strongly (P/R ≈ 0.91); the `invalid` class is the
limiting factor (P=0.75 / R=0.79) because it is the minority and more
heterogeneous — and it is the class that actually matters for filtering, so we do
**not** let the majority hide it.

Confusion matrix (rows = true, cols = predicted; order: invalid, valid):

```
            pred invalid   pred valid
true invalid     828          218
true valid       280         2652
```

**Secondary (imbalance-sensitive):** raw accuracy = 0.875, but the majority
baseline is already 0.737 and **balanced accuracy** (mean of per-class recall) is
**0.849** — so accuracy overstates performance by only ~2.6 points and should not
be read as the headline. Note ROC-AUC is mildly optimistic under imbalance;
per-class F1 above is the more reliable summary.

### Operating points

The decision threshold trades the classes off against each other. Reported with
**F1** (per-class and macro) since the classes are imbalanced; `kept%` is the
share of the test set predicted valid.

| threshold          | valid P | valid R | valid F1 | invalid F1 | macro F1  | kept%     |
|--------------------|---------|---------|----------|------------|-----------|-----------|
| 0.30               | 0.893   | 0.958   | 0.924    | 0.755      | 0.840     | 79.1%     |
| **0.40** (best F1) | 0.911   | 0.934   | 0.922    | **0.771**  | **0.847** | 75.6%     |
| 0.50               | 0.924   | 0.905   | 0.914    | 0.769      | 0.841     | 72.1%     |
| 0.60               | 0.940   | 0.863   | 0.900    | 0.758      | 0.829     | 67.6%     |
| 0.70               | 0.954   | 0.795   | 0.867    | 0.723      | 0.795     | 61.4%     |
| 0.80               | 0.968   | 0.674   | 0.794    | 0.658      | 0.726     | 51.3%     |
| 0.90               | 0.983   | 0.431   | 0.599    | 0.548      | 0.573     | 32.3%     |

**Macro-F1 peaks at threshold ≈ 0.40 (0.847)**, marginally above 0.50 (0.841), so
`MODEL_FILTER_THRESHOLD` defaults to 0.40 (F1-optimal). Use
a higher `MODEL_FILTER_THRESHOLD` for cleaner output (higher valid precision, more
junk caught) at the cost of dropping more borderline real names; the valid-F1 and
macro-F1 columns show where that trade-off stops paying off (both fall steadily
above 0.6).

---

## 7. Throughput

Measured by `sandbox/score_mentions.py` over the full 51,634-row CSV:

| mode                                    | rate                   | latency                 |
|-----------------------------------------|------------------------|-------------------------|
| **batch** (production / backfill)       | **50,300 rows/sec**    | 51,634 rows in 1,027 ms |
| **single** (streaming / live ingestion) | **2,598 mentions/sec** | 0.385 ms/mention        |

The ~130× gap is fixed per-call overhead (vectorization + predict) that amortizes
across a batch. Even single-call latency (0.4 ms) is negligible versus network/DB
cost during ingestion. Re-scoring the entire corpus is a ~1-second operation.

---

## 8. Full-corpus application

Scoring all 51,634 mention rows at threshold 0.5:

|         | count    | share   |
|---------|----------|---------|
| valid   | 42,794   | 82.9%   |
| invalid | 8,840    | 17.1%   |

(The valid share is higher than the 73.7% unique-name rate because popular real
tools — e.g. `ImageJ` — recur thousands of times and dominate the row count.)

### Applying to the stored corpus (backfill / re-score)

New mentions are scored automatically at ingestion (when `MODEL_FILTER_ENABLED`
is on). To populate the flags on mentions ingested **before** the model existed
— or to re-score everything after retraining — use the **Model filter** page at
`/model-filter` (linked from the dashboard), or its API directly:

| Method & path           | Effect                                                                 |
|-------------------------|------------------------------------------------------------------------|
| `GET /api/model/stats`  | Read-only: total mentions, how many are scored, how many flagged invalid, distinct names, active threshold, and whether enforcement is on. |
| `POST /api/model/reapply` | Re-scores every stored mention and rewrites `model_score` / `model_invalid` at `MODEL_FILTER_THRESHOLD` (default 0.4). |

`reapply` scores the **distinct** names once (batched — see §7) and fans the
results back to every mention in a single server-side AQL `UPDATE`. It is
idempotent for a fixed model+threshold and degrades to a logged no-op if the
model file is unavailable. Flags are always written; they only affect outbound
notifications while `MODEL_FILTER_ENABLED` is on. This mirrors the blacklist's
`POST /api/blacklist/reapply`.

---

## 9. Known limitations

- **Minority `invalid` class is weaker** (P=0.75): more diverse, fewer examples.
- **Irreducible grey zone**: lists that locally look name-like
  (`Cluster Arras Cluster Cambrai` ≈ 0.54) and bare acronyms (`ASEAN` ≈ 0.50) sit
  at the boundary — the same cases human and LLM labelers disagreed on.
- **Label provenance is mostly LLM** (Sonnet), validated against a 180-row human
  seed at 90% agreement, not a large independent human test set.
- **Policy is structural**, so genuinely novel but oddly-formatted real tools can
  be scored invalid; tune `MODEL_FILTER_THRESHOLD` down to be more permissive.

---

## 10. Reproduction

```bash
# (1) deps (already in pyproject runtime deps)
uv sync

# (2) train + evaluate (prints CV, held-out metrics, operating points) and save
python sandbox/train_classifier.py

# (3) sanity-check individual names
python sandbox/train_classifier.py --predict "ImageJ" "**** ***" "DESeq2 R"

# (4) score a full mentions CSV + measure throughput
python sandbox/score_mentions.py --input path/to/DOC_SOFTWARE_MENTIONS.csv

# (5) ship the retrained model with the app
cp sandbox/name_classifier.joblib app/static/data/name_classifier.joblib
```

Artifacts:

| File | Role |
|---|---|
| `sandbox/training_data.csv` | labeled dataset (`name,label,source`) |
| `sandbox/train_classifier.py` | training / evaluation / prediction |
| `sandbox/score_mentions.py` | full-CSV scoring + throughput measurement |
| `app/static/data/name_classifier.joblib` | trained model shipped with the app |
