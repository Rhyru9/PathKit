#!/usr/bin/env python3
"""
freeze_dataset.py — Freeze the dataset split and emit a hash-verified manifest.

FAIL-CLOSED behavior:
    - If frozen artifacts already exist, this script verifies their hashes and
      exits WITHOUT rewriting (no silent mutation of the "immutable" test set).
    - Overwriting requires an explicit --force flag.
    - Before writing, it validates row count, label vocabulary, and duplicate
      paths.

Produces:
    data/manifest.json        — counts, hashes, split definition (machine-readable)
    data/frozen/test_set.csv  — immutable copy of the held-out ground truth
    data/frozen/SHA256SUMS    — hashes of all frozen artifacts

Usage:
    python scripts/freeze_dataset.py            # freeze (or verify if frozen)
    python scripts/freeze_dataset.py --force    # overwrite existing freeze
"""

import argparse
import csv
import hashlib
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA = PROJECT_ROOT / "data"
FROZEN = DATA / "frozen"

# Valid 7-class label vocabulary (must match models/slugs/constants.py CLASSES)
VALID_LABELS = {"slug", "api", "asset", "search", "random_id", "file", "encoded"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_lines(path: Path) -> list[str]:
    with open(path, encoding="utf-8", errors="replace") as f:
        return [line.strip() for line in f if line.strip()]


def load_held_out(path: Path) -> list[tuple[str, str]]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            p = (r.get("path") or "").strip()
            lbl = (r.get("label") or "").strip()
            if p and lbl:
                rows.append((p, lbl))
    return rows


def validate_held_out(rows: list[tuple[str, str]], expected: int) -> None:
    """Fail loudly on any inconsistency in the held-out ground truth."""
    paths = [p for p, _ in rows]
    labels = [lbl for _, lbl in rows]

    if len(rows) != expected:
        print(f"ERROR: expected {expected} held-out rows, found {len(rows)}")
        sys.exit(1)

    dupes = {p for p in paths if paths.count(p) > 1}
    if dupes:
        print(f"ERROR: {len(dupes)} duplicate paths in held-out set:")
        for p in list(dupes)[:5]:
            print(f"  {p}")
        sys.exit(1)

    invalid = {lbl for lbl in labels if lbl not in VALID_LABELS}
    if invalid:
        print(f"ERROR: invalid labels: {sorted(invalid)}")
        print(f"       valid labels: {sorted(VALID_LABELS)}")
        sys.exit(1)

    print(f"Validated: {len(rows)} rows, no duplicates, all labels in vocabulary")


def read_expected_hash(sums_file: Path, rel: str) -> str | None:
    """Look up the expected hash for a file from SHA256SUMS."""
    if not sums_file.exists():
        return None
    for line in sums_file.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] == rel:
            return parts[0]
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing frozen artifacts (default: fail-closed)")
    args = parser.parse_args()

    paths_file = DATA / "paths.txt"
    endpoints_file = DATA / "endpoints.txt"
    labels_file = DATA / "annotate" / "sample_labeled.csv"

    # ── Load + validate ──────────────────────────
    paths = load_lines(paths_file)
    endpoints = load_lines(endpoints_file)
    held_out = load_held_out(labels_file)
    validate_held_out(held_out, expected=500)

    held_paths = {p for p, _ in held_out}
    train_pool = [p for p in paths if p not in held_paths]

    # ── Fail-closed: refuse to rewrite an existing freeze ──
    frozen_test = FROZEN / "test_set.csv"
    sums_file = FROZEN / "SHA256SUMS"

    if frozen_test.exists() and not args.force:
        existing_hash = sha256(frozen_test)
        expected = read_expected_hash(sums_file, "data/frozen/test_set.csv")
        if expected is not None and existing_hash == expected:
            print("Already frozen — hash verified. Exiting without rewrite.")
            print("Use --force to overwrite the frozen test set.")
            return 0
        print("ERROR: frozen artifact exists but hash does not match SHA256SUMS.")
        print("       The freeze is inconsistent. Inspect manually or use --force.")
        return 1

    if frozen_test.exists() and args.force:
        print("WARNING: --force given. Overwriting existing frozen test set.")

    # ── Write frozen test set ─────────────────────
    FROZEN.mkdir(parents=True, exist_ok=True)
    with open(frozen_test, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "path", "label"])
        for i, (p, lbl) in enumerate(held_out, 1):
            w.writerow([i, p, lbl])
    test_hash = sha256(frozen_test)

    # ── Reconciliation: paths vs endpoints ────────
    import re
    segments = set()
    for e in endpoints:
        for seg in re.split(r"/", e):
            seg = seg.strip()
            if seg:
                segments.add(seg)
    in_endpoints = len(set(paths) & segments)

    # ── Manifest (honest about label quality) ─────
    manifest = {
        "name": "PathKit URL Path Token Dataset",
        "version": "2.0",
        "frozen": True,
        "seed": args.seed,
        "hashes": {
            "data/paths.txt": sha256(paths_file),
            "data/endpoints.txt": sha256(endpoints_file),
            "data/annotate/sample_labeled.csv": sha256(labels_file),
            "data/frozen/test_set.csv": test_hash,
        },
        "counts": {
            "paths": len(paths),
            "endpoints": len(endpoints),
            "train_pool": len(train_pool),
        },
        "split": {
            "train": {
                "size": len(train_pool),
                "label": "weak-auto-label (heuristic)",
                "status": "training-pool",
                "note": "paths.txt minus held-out; auto-labeled for training only",
            },
            "validation": {
                "size": 0,
                "label": "none",
                "status": "not-created",
                "note": "separate development sample still required before paper",
            },
            "test": {
                "size": len(held_out),
                "label": "heuristic-assisted-single-annotator",
                "status": "development-held-out-not-clean",
                "path": "data/frozen/test_set.csv",
                "note": "labels were heuristic-assisted and reviewed by 1 annotator;"
                        "iterated on during detector tuning; NOT a clean "
                        "independently-annotated test set",
            },
        },
        "reconciliation": {
            "endpoints": len(endpoints),
            "unique_segments_in_endpoints": len(segments),
            "paths_in_endpoints": in_endpoints,
            "paths_not_in_endpoints": len(paths) - in_endpoints,
            "note": "paths.txt is a curated subset, NOT a pure segment-decomposition of endpoints.txt",
        },
        "provenance_confidence": "partial — exact crawl parameters still to be re-recorded",
    }

    (DATA / "manifest.json").write_text(
        __import__("json").dumps(manifest, indent=2), encoding="utf-8"
    )

    # ── SHA256SUMS ────────────────────────────────
    sums = [f"{h}  {rel}" for rel, h in manifest["hashes"].items()]
    sums_file.write_text("\n".join(sums) + "\n", encoding="utf-8")

    # ── Report ────────────────────────────────────
    print(f"Frozen test set: {len(held_out)} rows -> data/frozen/test_set.csv")
    print("Manifest -> data/manifest.json")
    print(f"Split: train={len(train_pool)}  test={len(held_out)}  (seed={args.seed})")
    print(f"Reconciliation: {in_endpoints:,}/{len(paths):,} paths "
          f"({in_endpoints / len(paths) * 100:.1f}%) overlap endpoints segments")
    return 0


if __name__ == "__main__":
    sys.exit(main())
