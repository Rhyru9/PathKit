#!/usr/bin/env python3
"""
sample_annotate.py — Generate a deterministic, stratified sample for manual annotation.

Usage:
    python scripts/sample_annotate.py [--n 500] [--seed 42]

Writes data/annotate/sample.csv with columns: id,path,label (label empty).
The same seed always produces the same sample — reproducible.
"""

import argparse
import csv
import random
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_paths(path: Path) -> list[str]:
    with open(path, encoding="utf-8", errors="replace") as f:
        return [line.strip() for line in f if line.strip()]


def bucket(path: str) -> str:
    """Stratify by rough structural type so the sample covers all shapes."""
    decoded = re.sub(r"%([0-9A-Fa-f]{2})", lambda m: chr(int(m.group(1), 16)), path)
    s = decoded.lower()

    if re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", s):
        return "uuid"
    if re.match(r"^\d{5,10}$", s):
        return "numeric"
    if re.search(r"\.[a-z]{2,5}$", s):
        return "file_ext"
    if "?" in s and "=" in s:
        return "query"
    if "-" in s or "_" in s:
        return "dashed"
    if "%" in path:
        return "encoded"
    return "other"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--input", default="data/paths.txt")
    parser.add_argument("--output", default="data/annotate/sample.csv")
    args = parser.parse_args()

    rng = random.Random(args.seed)

    paths = load_paths(PROJECT_ROOT / args.input)
    print(f"Loaded {len(paths):,} paths from {args.input}")

    # Stratify into buckets
    buckets: dict[str, list[str]] = {}
    for p in paths:
        buckets.setdefault(bucket(p), []).append(p)

    print("Bucket distribution:")
    for b, items in sorted(buckets.items(), key=lambda kv: -len(kv[1])):
        print(f"  {b:<12} {len(items):>6,}")

    # Proportional sample per bucket
    sample: list[str] = []
    for b, items in buckets.items():
        k = max(1, round(args.n * len(items) / len(paths)))
        k = min(k, len(items))
        sample.extend(rng.sample(items, k))

    # Trim/round to exact n
    if len(sample) > args.n:
        sample = rng.sample(sample, args.n)
    elif len(sample) < args.n:
        remaining = [p for p in paths if p not in set(sample)]
        sample.extend(rng.sample(remaining, args.n - len(sample)))

    rng.shuffle(sample)

    out = PROJECT_ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "path", "label"])
        for i, p in enumerate(sample, 1):
            writer.writerow([i, p, ""])

    print(f"\nWrote {len(sample)} samples -> {args.output}")
    print("Open the CSV and fill the 'label' column per guidelines.md.")


if __name__ == "__main__":
    main()
