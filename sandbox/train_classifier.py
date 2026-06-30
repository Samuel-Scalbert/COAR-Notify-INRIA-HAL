"""Train a fast software-name validity classifier from sandbox/training_data.csv.

Features: character n-grams (TF-IDF, word-boundary aware) — language-agnostic and
well suited to short strings, capturing both character distribution (garbage) and
subword/morpheme patterns (real names). Model: logistic regression (default) or
random forest, selectable via --model.

To compare two models, run training/eval once per model and compare the printed
metrics (the model name is shown in the output header):
    python sandbox/train_classifier.py --model logreg
    python sandbox/train_classifier.py --model rf

Usage:
    python sandbox/train_classifier.py                 # train logreg, evaluate, save
    python sandbox/train_classifier.py --model rf      # train random forest, evaluate, save
    python sandbox/train_classifier.py --predict "ImageJ" "**** ***" "DESeq2 R"
"""

import argparse
import csv
import os
import sys

import joblib  # model is self-generated locally and trusted; not loaded from untrusted sources

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "training_data.csv")
MODEL = os.path.join(HERE, "name_classifier.joblib")


def load(path):
    names, labels = [], []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            names.append(r["name"])
            labels.append(int(r["label"]))
    return names, labels


MODELS = ("logreg", "rf")


def build_pipeline(model_type="logreg"):
    """char_wb (2..5) n-grams + a classifier. Imported lazily so --predict is cheap.

    The TF-IDF feature step is identical across models so the saved Pipeline stays
    interchangeable for the consumer code, which only relies on predict_proba.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.pipeline import Pipeline

    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(2, 5),
        min_df=2,
        sublinear_tf=True,
        lowercase=False,  # case carries signal: "ImageJ" vs "image j"
    )

    if model_type == "logreg":
        from sklearn.linear_model import LogisticRegression

        clf = LogisticRegression(
            class_weight="balanced",  # offset 74/26 imbalance
            max_iter=2000,
            C=4.0,
        )
    elif model_type == "rf":
        from sklearn.ensemble import RandomForestClassifier

        # Trees on sparse high-dim char-ngram TF-IDF: many estimators help, and a
        # min_samples_leaf floor curbs overfitting to rare n-grams. n_jobs is bounded
        # (not -1) because cross_val_score already parallelises across folds, so
        # nesting -1 here would oversubscribe cores.
        clf = RandomForestClassifier(
            n_estimators=400,
            min_samples_leaf=2,
            class_weight="balanced",  # offset 74/26 imbalance
            n_jobs=2,
            random_state=42,
        )
    else:
        raise ValueError(f"unknown model_type {model_type!r}; choose from {MODELS}")

    return Pipeline([("tfidf", vectorizer), ("clf", clf)])


def train(model_type="logreg"):
    from sklearn.metrics import (
        balanced_accuracy_score,
        classification_report,
        confusion_matrix,
        f1_score,
        roc_auc_score,
    )
    from sklearn.model_selection import cross_val_score, train_test_split

    names, labels = load(DATA)
    print(
        f"model={model_type} — loaded {len(names)} examples — "
        f"valid={sum(labels)} invalid={len(labels) - sum(labels)}"
    )

    Xtr, Xte, ytr, yte = train_test_split(
        names, labels, test_size=0.2, stratify=labels, random_state=42
    )
    pipe = build_pipeline(model_type)

    # Quick 5-fold CV (macro-F1) on the training split for a stability estimate.
    cv = cross_val_score(pipe, Xtr, ytr, cv=5, scoring="f1_macro", n_jobs=-1)
    print(f"5-fold CV macro-F1 (train): {cv.mean():.3f} +/- {cv.std():.3f}")

    pipe.fit(Xtr, ytr)
    proba = pipe.predict_proba(Xte)[:, 1]
    pred = (proba >= 0.5).astype(int)

    # Classes are imbalanced, so lead with macro-F1 / balanced accuracy (per-class
    # precision/recall/F1 below) rather than plain accuracy, which is inflated by
    # the majority class (an always-"valid" baseline already scores ~0.74).
    print(f"\n=== held-out test (model={model_type}, threshold 0.5) ===")
    print(
        f"PRIMARY (imbalance-robust): macro-F1={f1_score(yte, pred, average='macro'):.3f}  "
        f"balanced-accuracy={balanced_accuracy_score(yte, pred):.3f}  "
        f"ROC-AUC={roc_auc_score(yte, proba):.3f}"
    )
    print(classification_report(yte, pred, target_names=["invalid", "valid"], digits=3))
    print("confusion matrix [rows=true, cols=pred] (invalid, valid):")
    print(confusion_matrix(yte, pred))

    # Operating-point table: how the metrics trade off as we move the threshold.
    # Reported with F1 (per-class + macro) since the classes are imbalanced; the
    # best threshold is the one that maximizes macro-F1, not valid precision alone.
    # Higher threshold -> keep fewer names but cleaner (fewer junk kept as valid).
    print("\n=== operating points (decision = 'valid' if proba >= t) ===")
    print(
        f"{'thresh':>7} {'valid_P':>8} {'valid_R':>8} {'valid_F1':>9} "
        f"{'invalid_F1':>11} {'macro_F1':>9} {'kept%':>7}"
    )
    from sklearn.metrics import precision_score, recall_score

    for t in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
        p = (proba >= t).astype(int)
        vp = precision_score(yte, p, pos_label=1, zero_division=0)
        vr = recall_score(yte, p, pos_label=1, zero_division=0)
        vf1 = f1_score(yte, p, pos_label=1, zero_division=0)
        if1 = f1_score(yte, p, pos_label=0, zero_division=0)
        mf1 = f1_score(yte, p, average="macro", zero_division=0)
        print(
            f"{t:>7.2f} {vp:>8.3f} {vr:>8.3f} {vf1:>9.3f} "
            f"{if1:>11.3f} {mf1:>9.3f} {p.mean() * 100:>6.1f}%"
        )

    # Refit on ALL data before saving — more data, better final model.
    pipe.fit(names, labels)
    joblib.dump(pipe, MODEL)
    print(f"\nsaved model -> {MODEL}")
    return pipe


def predict(items):
    if not os.path.exists(MODEL):
        raise SystemExit("No model found. Run without --predict first to train.")
    pipe = joblib.load(MODEL)
    proba = pipe.predict_proba(items)[:, 1]
    for name, pr in zip(items, proba, strict=False):
        verdict = "valid" if pr >= 0.5 else "invalid"
        print(f"  {pr:.3f}  {verdict:7}  {name!r}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--model",
        choices=MODELS,
        default="logreg",
        help="Classifier to train/evaluate/save (default: logreg).",
    )
    ap.add_argument("--predict", nargs="+", help="Classify the given name strings using the saved model.")
    args = ap.parse_args()
    if args.predict:
        predict(args.predict)
    else:
        train(args.model)


if __name__ == "__main__":
    sys.exit(main())
