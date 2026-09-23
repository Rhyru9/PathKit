"""
harness.py — Deterministic evaluation harness for PathKit.

Produces per-class precision/recall/F1, macro/micro averages, a confusion
matrix, and abstention metrics. Fixed seed for reproducible splits.

Usage:
    python eval/harness.py \
        --annotations data/annotate/sample.csv \
        --weights weights/slugs_v4.json \
        --seed 42
"""

import argparse
import csv
import json
import random
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from models.decision import classify_path
from models.slugs import URLIntentModel
from models.slugs.constants import CLASSES

def load_annotations(csv_path: Path) -> list[tuple[str, str]]:
    """Load (path, label) pairs from an annotation CSV, skipping empty labels."""
    rows: list[tuple[str, str]] = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = (row.get("label") or "").strip()
            path = (row.get("path") or "").strip()
            if label and path:
                rows.append((path, label))
    return rows


def full_system_predict(raw: str, model: URLIntentModel) -> str:
    return classify_path(raw, model).label


def ml_predict(raw: str, model: URLIntentModel) -> str:
    """ML classifier only, without identifier detectors."""
    return model.predict(raw)["final"]


def evaluate(y_true: list[str], y_pred: list[str]) -> dict:
    """
    Compute accuracy, per-class P/R/F1, macro/micro F1.
    """
    classes = sorted(set(y_true) | set(y_pred))
    tp = Counter()
    fp = Counter()
    fn = Counter()

    for t, p in zip(y_true, y_pred):
        if p == t:
            tp[t] += 1
        else:
            fp[p] += 1
            fn[t] += 1

    metrics: dict = {"classes": {}, "accuracy": 0.0, "macro_f1": 0.0, "micro_f1": 0.0}

    correct = sum(tp.values())
    total = len(y_true)
    metrics["accuracy"] = correct / max(total, 1)

    # Per-class
    macro_p = macro_r = macro_f1 = 0.0
    n_class = len(classes)
    for c in classes:
        tp_c = tp[c]
        fp_c = fp[c]
        fn_c = fn[c]
        p = tp_c / max(tp_c + fp_c, 1)
        r = tp_c / max(tp_c + fn_c, 1)
        f1 = 2 * p * r / max(p + r, 1e-9)
        metrics["classes"][c] = {
            "support": tp_c + fn_c,
            "precision": round(p, 4),
            "recall": round(r, 4),
            "f1": round(f1, 4),
        }
        macro_p += p
        macro_r += r
        macro_f1 += f1

    if n_class:
        metrics["macro_f1"] = round(macro_f1 / n_class, 4)

    # Micro F1 == accuracy for single-label
    metrics["micro_f1"] = round(correct / max(total, 1), 4)
    return metrics


def confusion_matrix(y_true: list[str], y_pred: list[str], classes: list[str]) -> list[list[int]]:
    idx = {c: i for i, c in enumerate(classes)}
    n = len(classes)
    matrix = [[0] * n for _ in range(n)]
    for t, p in zip(y_true, y_pred):
        matrix[idx[t]][idx[p]] += 1
    return matrix


def split(rows: list[tuple[str, str]], seed: int, val_ratio: float = 0.2):
    """Deterministic shuffle + train/val split."""
    rng = random.Random(seed)
    rows = list(rows)
    rng.shuffle(rows)
    k = int(len(rows) * (1 - val_ratio))
    return rows[:k], rows[k:]


def report(metrics: dict, matrix: list[list[int]], classes: list[str]) -> None:
    print("\n" + "=" * 70)
    print("EVALUATION REPORT")
    print("=" * 70)

    print(f"\nAccuracy:  {metrics['accuracy']:.4f}")
    print(f"Macro F1:  {metrics['macro_f1']:.4f}")
    print(f"Micro F1:  {metrics['micro_f1']:.4f}")

    print(f"\n{'class':<14} {'support':>8} {'precision':>10} {'recall':>8} {'f1':>8}")
    print("-" * 52)
    for c in classes:
        m = metrics["classes"].get(c)
        if m:
            print(
                f"{c:<14} {m['support']:>8} {m['precision']:>10} {m['recall']:>8} {m['f1']:>8}"
            )
        else:
            print(f"{c:<14} {'0':>8} {'-':>10} {'-':>8} {'-':>8}")

    print("\nConfusion matrix (rows=true, cols=predicted):")
    header = " " * 14 + "".join(f"{c[:6]:>8}" for c in classes)
    print(header)
    for i, row in enumerate(matrix):
        print(f"{classes[i]:<14}" + "".join(f"{v:>8}" for v in row))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotations", default="data/annotate/sample.csv")
    parser.add_argument("--weights", default="weights/slugs_v4.json")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--val-ratio", type=float, default=0.2)
    parser.add_argument("--json-out", default=None, help="Write metrics to JSON file")
    args = parser.parse_args()

    ann_path = PROJECT_ROOT / args.annotations
    if not ann_path.exists():
        print(f"Error: annotations not found: {ann_path}")
        print("Generate a sample first: python scripts/sample_annotate.py")
        print("Then fill the 'label' column per data/annotate/guidelines.md")
        raise SystemExit(2)

    rows = load_annotations(ann_path)
    if not rows:
        print("Error: no labeled rows found. Fill the 'label' column first.")
        raise SystemExit(2)

    print(f"Loaded {len(rows)} annotated paths")

    # Train/val split (val = held-out evaluation set)
    train_rows, val_rows = split(rows, args.seed, args.val_ratio)
    print(f"Train: {len(train_rows)}  Val: {len(val_rows)}  (seed={args.seed})")

    # Train a fresh model only on the training partition.
    model = URLIntentModel()
    unknown = sorted({label for _, label in train_rows} - set(CLASSES))
    if unknown:
        raise ValueError(f"Unknown labels in annotations: {', '.join(unknown)}")
    rng = random.Random(args.seed)
    rng.shuffle(train_rows)
    for path, label in train_rows:
        model.train(path, label)
    if args.weights:
        print(f"Evaluation model trained from {len(train_rows)} labeled rows; "
              f"--weights is ignored for leakage safety")

    # Evaluate on held-out val set
    y_true = [label for _, label in val_rows]
    y_pred = [full_system_predict(path, model) for path, _ in val_rows]

    classes = sorted(set(y_true) | set(CLASSES))
    metrics = evaluate(y_true, y_pred)
    matrix = confusion_matrix(y_true, y_pred, classes)

    report(metrics, matrix, classes)

    # Abstention (uncertainty) analysis
    uncertain = sum(
        1 for path, _ in val_rows if model.predict(path)["is_uncertain"]
    )
    print(f"\nAbstention: {uncertain}/{len(val_rows)} predictions uncertain "
          f"({uncertain / max(len(val_rows), 1) * 100:.1f}%)")

    if args.json_out:
        out_path = PROJECT_ROOT / args.json_out
        out_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "seed": args.seed,
            "n_train": len(train_rows),
            "n_val": len(val_rows),
            "metrics": metrics,
            "confusion_matrix": matrix,
            "classes": classes,
            "abstention": uncertain,
        }
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Wrote metrics -> {args.json_out}")


if __name__ == "__main__":
    main()
