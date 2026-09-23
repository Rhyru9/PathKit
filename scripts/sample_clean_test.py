#!/usr/bin/env python3
"""
sample_clean_test.py — Generate a FRESH, stratified clean test set for
independent manual annotation.

Unlike the earlier development sample, this one:
    - uses a NEW seed (default 2026, NOT 42);
    - draws from BOTH data/paths.txt and data/endpoints.txt so rare classes
      (api, search, encoded) are represented;
    - oversamples rare classes to a minimum count;
    - emits empty labels (for 2 independent annotators, no PathKit predictions).

Usage:
    python scripts/sample_clean_test.py [--n 600] [--seed 2026] [--out data/annotate/clean_test.csv]
"""

import argparse
import csv
import random
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA = PROJECT_ROOT / "data"

# Minimum samples per rare class (api/search/encoded are otherwise scarce).
MIN_PER_RARE = 30


def load_lines(path: Path) -> list[str]:
    with open(path, encoding="utf-8", errors="replace") as f:
        return [line.strip() for line in f if line.strip()]


def bucket(path: str) -> str:
    """Structural bucket (not label — no PathKit prediction)."""
    s = path.lower()
    if re.search(r"/api/|/rest/|/graphql", s):
        return "api"
    if "?" in s and "=" in s:
        return "query"
    if re.search(r"%[0-9A-Fa-f]{2}", path):
        return "encoded"
    if re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", s):
        return "uuid"
    if re.match(r"^\d{5,10}$", s):
        return "numeric"
    if re.search(r"\.[a-z]{2,5}$", s):
        return "file_ext"
    if "-" in s or "_" in s:
        return "dashed"
    return "other"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=600)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--out", default="data/annotate/clean_test.csv")
    args = parser.parse_args()
    minimum_size = 3 * MIN_PER_RARE
    if args.n < minimum_size:
        parser.error(f"--n must be at least {minimum_size} to preserve rare-class floors")

    rng = random.Random(args.seed)

    paths = load_lines(DATA / "paths.txt")
    endpoints = load_lines(DATA / "endpoints.txt")

    # Pool = paths + endpoints (endpoints contribute api/query rare classes).
    # Deduplicate while preserving order.
    pool = list(dict.fromkeys(paths + endpoints))

    # ── Stratify ───────────────────────────────────
    buckets: dict[str, list[str]] = {}
    for p in pool:
        buckets.setdefault(bucket(p), []).append(p)

    print("Bucket distribution (pool):")
    for b, items in sorted(buckets.items(), key=lambda kv: -len(kv[1])):
        print(f"  {b:<12} {len(items):>7,}")

    # ── Sample with rare-class floor ───────────────
    sample: list[str] = []
    used: set[str] = set()

    # 1. Rare classes: guarantee MIN_PER_RARE each.
    for rare in ("api", "query", "encoded"):
        items = [p for p in buckets.get(rare, []) if p not in used]
        k = min(MIN_PER_RARE, len(items))
        chosen = rng.sample(items, k)
        sample.extend(chosen)
        used.update(chosen)
        print(f"  rare {rare:<10} sampled {len(chosen):>3}")

    # 2. Fill the rest from the remaining pool.
    remaining = [p for p in pool if p not in used]
    need = args.n - len(sample)
    if need > 0:
        sample.extend(rng.sample(remaining, min(need, len(remaining))))

    rng.shuffle(sample)
    sample = sample[: args.n]

    # ── Write CSV (empty labels for annotators) ────
    out = PROJECT_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "path", "label_a", "label_b"])
        for i, p in enumerate(sample, 1):
            w.writerow([i, p, "", ""])

    print(f"\nWrote {len(sample)} samples -> {args.out}")
    print("Two annotators fill label_a and label_b independently;")
    print("then run scripts/agreement.py to measure Cohen's kappa.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
