"""
ablations.py — Detector/feature ablation study for PathKit.

Runs the full hybrid pipeline and each ablation variant on the SAME
development-held-out split, reporting accuracy, macro-F1, per-class F1, and
the delta vs. the full hybrid (negative delta = removing that stage hurts).

Ablation variants:
    full_hybrid    — canonical PathKit
    no_encoding    — disable encoding/routing-escape detector (decode remains)
    no_uuid        — disable UUID detector
    no_timestamp   — disable timestamp detector
    no_hash_base64 — disable hash + base64 detectors
    no_other       — disable "other" (routing/ID/file-ext) detector
    rule_only      — detectors + majority fallback (no ML)
    ml_only        — ML classifier with all detectors disabled

Usage:
    python eval/ablations.py [--annotations ...] [--seed 42] \
                             [--json-out output/ablation_results.json]
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from eval.baselines import auto_label_pool, load_paths
from eval.harness import confusion_matrix, evaluate, load_annotations
from models.decision import classify_path
from models.slugs import URLIntentModel
from models.slugs.constants import CLASSES

ALL_DETECTORS = frozenset({"encoding", "search", "uuid", "timestamp", "hash", "base64", "other"})

# name -> (disabled set, fallback_label)
ABLATIONS = [
    ("full_hybrid", frozenset(), None),
    ("no_encoding", frozenset({"encoding"}), None),
    ("no_uuid", frozenset({"uuid"}), None),
    ("no_timestamp", frozenset({"timestamp"}), None),
    ("no_hash_base64", frozenset({"hash", "base64"}), None),
    ("no_other", frozenset({"other"}), None),
    ("rule_only", frozenset(), "MAJORITY"),
    ("ml_only", ALL_DETECTORS, None),
]


def run_ablation(held_out: list[tuple[str, str]], train_pool: list[tuple[str, str]],
                 seed: int) -> dict:
    from collections import Counter

    y_true = [lbl for _, lbl in held_out]
    eval_paths = [p for p, _ in held_out]
    majority = Counter(lbl for _, lbl in train_pool).most_common(1)[0][0]

    # Train ML model on the auto-labeled pool.
    model = URLIntentModel()
    import random
    rng = random.Random(seed)
    train = list(train_pool)
    rng.shuffle(train)
    for path, label in train:
        model.train(path, label)

    classes = sorted(set(y_true) | set(CLASSES))
    results: dict = {
        "seed": seed,
        "n_train": len(train_pool),
        "n_held_out": len(held_out),
        "majority": majority,
        "evaluation_status": "development-held-out-heuristic-assisted",
        "no_encoding_disables": "routing-escape-detector-only",
        "variants": {},
    }

    for name, disabled, fallback in ABLATIONS:
        fb = majority if fallback == "MAJORITY" else fallback
        y_pred = [classify_path(p, model, fallback_label=fb, disabled=disabled).label
                  for p in eval_paths]
        metrics = evaluate(y_true, y_pred)
        matrix = confusion_matrix(y_true, y_pred, classes)
        results["variants"][name] = {
            "accuracy": metrics["accuracy"],
            "macro_f1": metrics["macro_f1"],
            "per_class": metrics["classes"],
            "confusion_matrix": matrix,
        }

    # Deltas are descriptive differences on this development split, not
    # causal estimates of detector value.
    full = results["variants"]["full_hybrid"]
    for name, v in results["variants"].items():
        if name == "full_hybrid":
            continue
        v["delta_accuracy"] = round(v["accuracy"] - full["accuracy"], 4)
        v["delta_macro_f1"] = round(v["macro_f1"] - full["macro_f1"], 4)

    results["classes"] = classes
    return results


def report(results: dict) -> None:
    classes = results["classes"]
    print("=" * 74)
    print(f"ABLATION STUDY  (n_train={results['n_train']:,}, n_held_out={results['n_held_out']}, "
          f"seed={results['seed']})")
    print("=" * 74)

    print(f"\n{'variant':<16} {'acc':>7} {'Δacc':>7} {'macro-F1':>9} {'ΔF1':>7}")
    print("-" * 52)
    for name, v in results["variants"].items():
        dacc = v.get("delta_accuracy", 0.0)
        df1 = v.get("delta_macro_f1", 0.0)
        print(f"{name:<16} {v['accuracy']:>7.4f} {dacc:>+7.4f} "
              f"{v['macro_f1']:>9.4f} {df1:>+7.4f}")

    # Per-class F1 (for the classes each detector targets)
    print("\nPer-class F1 (development-held-out; heuristic-assisted labels):")
    header = f"{'class':<14}" + "".join(f"{n[:10]:>12}" for n, _, _ in ABLATIONS)
    print(header)
    print("-" * len(header))
    for c in classes:
        row = f"{c:<14}"
        for name, _, _ in ABLATIONS:
            m = results["variants"][name]["per_class"].get(c, {})
            row += f"{m.get('f1', 0.0):>12.4f}"
        print(row)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/paths.txt")
    parser.add_argument("--annotations", default="data/annotate/sample_labeled.csv")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--json-out", default="output/ablation_results.json")
    args = parser.parse_args()

    ann_path = PROJECT_ROOT / args.annotations
    in_path = PROJECT_ROOT / args.input
    if not ann_path.exists() or not in_path.exists():
        print("Error: annotations or input file not found.")
        return 2

    held_out = load_annotations(ann_path)
    all_paths = load_paths(in_path)
    held_paths = {p for p, _ in held_out}
    train_pool = auto_label_pool([p for p in all_paths if p not in held_paths])

    print(f"Train pool (auto-labeled): {len(train_pool):,}")
    print(f"Development-held-out (heuristic-assisted): {len(held_out)}")

    results = run_ablation(held_out, train_pool, args.seed)
    report(results)

    out = PROJECT_ROOT / args.json_out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nWrote -> {args.json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
