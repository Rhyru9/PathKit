#!/usr/bin/env python3
"""
agreement.py — Measure inter-annotator agreement (Cohen's kappa) between two
independent label columns in a clean-test CSV.

Input: a CSV with columns id,path,label_a,label_b (as produced by
sample_clean_test.py). Rows where either label is empty are skipped.

Output: observed agreement, expected agreement, Cohen's kappa, per-label
confusion, and a list of disagreements for adjudication.

Usage:
    python scripts/agreement.py --csv data/annotate/clean_test.csv
"""

import argparse
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VALID_LABELS = {"slug", "api", "asset", "search", "random_id", "file", "encoded"}


def cohens_kappa(a: list[str], b: list[str]) -> dict:
    """Compute Cohen's kappa + agreement statistics."""
    n = len(a)
    if n == 0:
        return {"n": 0, "observed": 0.0, "expected": 0.0, "kappa": 0.0}

    # Observed agreement
    observed = sum(1 for x, y in zip(a, b) if x == y) / n

    # Expected agreement (chance)
    ca = Counter(a)
    cb = Counter(b)
    expected = sum((ca[l] / n) * (cb[l] / n) for l in set(a) | set(b))

    kappa = (observed - expected) / (1 - expected) if expected < 1 else 1.0
    return {"n": n, "observed": round(observed, 4), "expected": round(expected, 4),
            "kappa": round(kappa, 4)}


def interpret(kappa: float) -> str:
    if kappa < 0:
        return "poor (worse than chance)"
    if kappa < 0.20:
        return "slight"
    if kappa < 0.40:
        return "fair"
    if kappa < 0.60:
        return "moderate"
    if kappa < 0.80:
        return "substantial"
    return "almost perfect"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="data/annotate/clean_test.csv")
    args = parser.parse_args()

    path = PROJECT_ROOT / args.csv
    if not path.exists():
        print(f"Error: {path} not found.")
        return 2

    a: list[str] = []
    b: list[str] = []
    disagreements: list[tuple[str, str, str]] = []
    seen_paths: set[str] = set()
    invalid: list[tuple[str, str]] = []

    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            la = (row.get("label_a") or "").strip()
            lb = (row.get("label_b") or "").strip()
            p = (row.get("path") or "").strip()
            if p in seen_paths:
                print(f"Error: duplicate path at row {row.get('id', '?')}.")
                return 2
            if p:
                seen_paths.add(p)
            if la and lb:
                if la not in VALID_LABELS or lb not in VALID_LABELS:
                    invalid.append((row.get("id", "?"), f"{la}/{lb}"))
                    continue
                a.append(la)
                b.append(lb)
                if la != lb:
                    disagreements.append((row.get("id", "?"), la, lb))

    if invalid:
        print(f"Error: invalid labels in {len(invalid)} rows; expected: "
              f"{', '.join(sorted(VALID_LABELS))}")
        return 2
    if not a:
        print("Error: no rows have labels from both annotators.")
        return 2

    stats = cohens_kappa(a, b)

    print("=" * 60)
    print("INTER-ANNOTATOR AGREEMENT (Cohen's kappa)")
    print("=" * 60)
    print(f"  Labeled by both: {stats['n']}")
    print(f"  Observed agreement: {stats['observed']:.4f}")
    print(f"  Expected agreement: {stats['expected']:.4f}")
    print(f"  Cohen's kappa:      {stats['kappa']:.4f}")
    print(f"  Interpretation:     {interpret(stats['kappa'])}")

    # Per-label confusion (A rows, B cols)
    labels = sorted(set(a) | set(b))
    conf = defaultdict(Counter)
    for x, y in zip(a, b):
        conf[x][y] += 1

    print(f"\n{'A\\B':<14}" + "".join(f"{l[:6]:>8}" for l in labels))
    for x in labels:
        print(f"{x:<14}" + "".join(f"{conf[x][y]:>8}" for y in labels))

    print(f"\nDisagreements ({len(disagreements)}):")
    for row_id, la, lb in disagreements[:20]:
        print(f"  row={row_id:<6} A={la:<10} B={lb:<10}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
