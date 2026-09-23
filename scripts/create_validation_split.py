#!/usr/bin/env python3
"""Create a deterministic weak-label validation split without publishing paths.

The validation rows are sampled from paths.txt after excluding the frozen
development-held-out rows. The emitted CSV stays ignored because it contains
crawled paths; data/splits.json records only the reproducibility metadata.
"""

import argparse
import csv
import hashlib
import json
import random
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from eval.baselines import auto_label_pool, load_paths
from eval.harness import load_annotations


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/paths.txt")
    parser.add_argument("--annotations", default="data/annotate/sample_labeled.csv")
    parser.add_argument("--seed", type=int, default=2027)
    parser.add_argument("--ratio", type=float, default=0.2)
    parser.add_argument("--output", default="data/validation/weak_validation.csv")
    parser.add_argument("--metadata", default="data/splits.json")
    args = parser.parse_args()
    if not 0 < args.ratio < 1:
        parser.error("--ratio must be between 0 and 1")

    input_path = PROJECT_ROOT / args.input
    annotation_path = PROJECT_ROOT / args.annotations
    rows = load_annotations(annotation_path)
    held_out = {path for path, _ in rows}
    candidates = [path for path in load_paths(input_path) if path not in held_out]
    weak_rows = auto_label_pool(candidates)
    if not weak_rows:
        raise SystemExit("No weak-labeled candidates available")

    rng = random.Random(args.seed)
    rng.shuffle(weak_rows)
    size = max(1, round(len(weak_rows) * args.ratio))
    validation = weak_rows[:size]
    validation_paths = {path for path, _ in validation}

    output_path = PROJECT_ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["path", "label"])
        writer.writerows(validation)

    metadata_path = PROJECT_ROOT / args.metadata
    metadata = {
        "seed": args.seed,
        "ratio": args.ratio,
        "source": args.input,
        "source_sha256": sha256(input_path),
        "held_out_source": args.annotations,
        "candidate_weak_rows": len(weak_rows),
        "validation_rows": len(validation),
        "validation_path_sha256": sha256(output_path),
        "label_status": "weak-auto-label",
        "raw_output": args.output,
        "excluded_held_out_rows": len(held_out),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"Validation rows: {len(validation):,}")
    print(f"Excluded development-held-out paths: {len(held_out):,}")
    print(f"CSV (local/ignored): {args.output}")
    print(f"Metadata: {args.metadata}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
