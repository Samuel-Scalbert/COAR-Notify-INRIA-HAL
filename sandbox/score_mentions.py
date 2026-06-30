"""Score every software mention in the HAL CSV with the trained classifier.

Reads IDENTIFIANT,DOCID,SOFTWARE_NAME, predicts a validity score per row, writes
an output CSV with SCORE + VALID columns, and reports throughput (batch rows/sec
and single-item latency for streaming/ingestion use).

Usage:
    python sandbox/score_mentions.py --input ~/Downloads/DOC_SOFTWARE_MENTIONS.csv
"""

import argparse
import csv
import os
import time

import joblib  # model is self-generated locally and trusted

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(HERE, "name_classifier.joblib")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--input", required=True, help="Path to the mentions CSV.")
    ap.add_argument("--output", default=os.path.join(HERE, "scored_mentions.csv"))
    ap.add_argument("--threshold", type=float, default=0.5)
    args = ap.parse_args()

    pipe = joblib.load(MODEL)

    with open(os.path.expanduser(args.input), newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    names = [r["SOFTWARE_NAME"] for r in rows]
    print(f"loaded {len(names)} rows")

    # --- Batch scoring (the production path: vectorize + predict in one shot) ---
    t0 = time.perf_counter()
    proba = pipe.predict_proba(names)[:, 1]
    batch_dt = time.perf_counter() - t0
    rps = len(names) / batch_dt

    for r, p in zip(rows, proba):
        r["SCORE"] = f"{p:.4f}"
        r["VALID"] = int(p >= args.threshold)

    fieldnames = list(rows[0].keys())
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    valid = sum(1 for r in rows if r["VALID"] == 1)
    print(f"\nwrote {len(rows)} scored rows -> {args.output}")
    print(f"  valid:   {valid} ({valid / len(rows) * 100:.1f}%)")
    print(f"  invalid: {len(rows) - valid} ({(len(rows) - valid) / len(rows) * 100:.1f}%)")

    # --- Single-item latency (streaming path: one mention at a time) ---
    sample = names[:1000]
    t0 = time.perf_counter()
    for n in sample:
        pipe.predict_proba([n])
    single_dt = time.perf_counter() - t0
    per_item_ms = single_dt / len(sample) * 1000

    print("\n=== throughput ===")
    print(f"  batch:  {len(names)} rows in {batch_dt * 1000:.1f} ms  ->  {rps:,.0f} rows/sec")
    print(f"  single: {len(sample)} one-at-a-time  ->  {per_item_ms:.3f} ms/mention  ({1000 / per_item_ms:,.0f}/sec)")


if __name__ == "__main__":
    main()
