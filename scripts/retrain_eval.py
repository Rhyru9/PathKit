#!/usr/bin/env python3
"""
retrain_eval.py — Retrain the ML classifier on the CURRENT dataset while
excluding the held-out ground-truth set, then report eval metrics.

This prevents label leakage: the 500 manually-labeled paths are NEVER used
for auto-labeling or training. The model is trained only on auto-labeled
data from the remaining paths.

Usage:
    python scripts/retrain_eval.py \
        --annotations data/annotate/sample_labeled.csv \
        --input data/paths.txt \
        --weights-out weights/slugs_v5.json \
        --seed 42
"""

import argparse
import csv
import random
import re
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from models.slugs import URLIntentModel
from models.slugs.constants import CLASSES
from models.slugs.labeling import auto_label
from models.encoding import decode

from eval.harness import evaluate, confusion_matrix, full_system_predict


def load_held_out(annotations: Path) -> set[str]:
    """Return the set of raw paths that are held out (never used for training)."""
    held = set()
    with open(annotations, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            path = (row.get("path") or "").strip()
            if path:
                held.add(path)
    return held


def load_all(input_path: Path) -> list[str]:
    with open(input_path, encoding="utf-8", errors="replace") as f:
        return [line.strip() for line in f if line.strip()]


def auto_label_paths(paths: list[str]) -> list[tuple[str, str]]:
    """Auto-label + negative examples (same logic as pipeline)."""
    train_data = []
    for raw in paths:
        label = auto_label(raw)
        if label:
            train_data.append((raw, label))
            continue
        s = decode(raw).lower()
        if re.match(r"^[0-9a-f]{8}-", s):
            train_data.append((raw, "random_id"))
        elif "-" not in s and len(s) < 15 and not s.isalpha():
            train_data.append((raw, "file"))
    return train_data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotations", default="data/annotate/sample_labeled.csv")
    parser.add_argument("--input", default="data/paths.txt")
    parser.add_argument("--weights-out", default="weights/slugs_v5.json")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    held = load_held_out(PROJECT_ROOT / args.annotations)
    all_paths = load_all(PROJECT_ROOT / args.input)

    # Exclude held-out from training
    train_paths = [p for p in all_paths if p not in held]
    n_held_in_data = len(all_paths) - len(train_paths)

    print(f"All paths:      {len(all_paths):,}")
    print(f"Held-out:       {len(held):,} ({n_held_in_data} found in data)")
    print(f"Training pool:  {len(train_paths):,}")

    # Auto-label training pool
    train_data = auto_label_paths(train_paths)
    print(f"\nAuto-labeled:   {len(train_data):,}")
    for cls, cnt in Counter(label for _, label in train_data).most_common():
        print(f"  {cls:<12} {cnt:>6,}")

    # Train
    rng = random.Random(args.seed)
    rng.shuffle(train_data)

    model = URLIntentModel()
    print(f"\nTraining on {len(train_data):,} examples (seed={args.seed})...")
    for raw, label in train_data:
        model.train(raw, label)

    # Save weights
    out = PROJECT_ROOT / args.weights_out
    out.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(out))
    print(f"Saved -> {args.weights_out}")

    # Evaluate on held-out ground truth (full system: detectors + ML)
    y_true = []
    y_pred = []
    with open(PROJECT_ROOT / args.annotations, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            path = (row.get("path") or "").strip()
            label = (row.get("label") or "").strip()
            if path and label:
                y_true.append(label)
                y_pred.append(full_system_predict(path, model))

    classes = sorted(set(y_true) | set(CLASSES))
    metrics = evaluate(y_true, y_pred)
    matrix = confusion_matrix(y_true, y_pred, classes)

    print("\n" + "=" * 70)
    print("HELD-OUT EVALUATION (full system: detectors + ML)")
    print("=" * 70)
    print(f"Accuracy:  {metrics['accuracy']:.4f}")
    print(f"Macro F1:  {metrics['macro_f1']:.4f}")
    print(f"Micro F1:  {metrics['micro_f1']:.4f}")

    print(f"\n{'class':<14} {'support':>8} {'precision':>10} {'recall':>8} {'f1':>8}")
    print("-" * 52)
    for c in classes:
        m = metrics["classes"].get(c)
        if m and m["support"] > 0:
            print(f"{c:<14} {m['support']:>8} {m['precision']:>10} {m['recall']:>8} {m['f1']:>8}")

    print("\nConfusion matrix (rows=true, cols=predicted):")
    header = " " * 14 + "".join(f"{c[:6]:>8}" for c in classes)
    print(header)
    for i, row in enumerate(matrix):
        print(f"{classes[i]:<14}" + "".join(f"{v:>8}" for v in row))


if __name__ == "__main__":
    main()
