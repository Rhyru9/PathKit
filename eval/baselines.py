"""
baselines.py — Benchmark PathKit against three baselines on identical data.

Baselines (all evaluated on the SAME 500-row development-held-out set):
    1. majority  — always predict the auto-labeled training majority class
    2. rule-only — detector pipeline with majority-class fallback (no ML)
    3. ml-only   — URLIntentModel trained on auto-labeled pool, no detectors
    4. hybrid    — canonical PathKit (detectors + ML), via models.decision

The ML model is trained on the auto-labeled training pool (paths.txt minus the
500 held-out), matching the production training protocol. Reports accuracy,
95% CI (Wilson), macro-F1, per-class P/R/F1, confusion matrix, abstention,
and support.

Usage:
    python eval/baselines.py [--input data/paths.txt] [--annotations ...] \
                             [--seed 42] [--json-out output/baseline_results.json]
"""

import argparse
import json
import math
import random
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from eval.harness import confusion_matrix, evaluate, load_annotations
from scripts.retrain_eval import auto_label_paths
from models.decision import classify_path
from models.slugs import URLIntentModel
from models.slugs.constants import CLASSES


# ── Data loading (production protocol) ─────────────


def load_paths(path: Path) -> list[str]:
    with open(path, encoding="utf-8", errors="replace") as f:
        return [line.strip() for line in f if line.strip()]


def auto_label_pool(paths: list[str]) -> list[tuple[str, str]]:
    """Use the canonical production labeling and UTF-8 decoding protocol."""
    return auto_label_paths(paths)


# ── Baselines ──────────────────────────────────────


def majority_predict(paths: list[str], majority: str) -> list[str]:
    return [majority] * len(paths)


def rule_only_predict(paths: list[str], model: URLIntentModel, majority: str) -> list[str]:
    return [classify_path(p, model, fallback_label=majority).label for p in paths]


def ml_only_predict(paths: list[str], model: URLIntentModel) -> list[str]:
    return [model.predict(p)["final"] for p in paths]


def hybrid_predict(paths: list[str], model: URLIntentModel) -> list[str]:
    return [classify_path(p, model).label for p in paths]


# ── Confidence interval (Wilson, 95%) ──────────────


def wilson_ci(correct: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return (0.0, 0.0)
    p = correct / total
    denom = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    margin = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


# ── Benchmark runner ───────────────────────────────


def run_benchmark(held_out: list[tuple[str, str]], train_pool: list[tuple[str, str]],
                  seed: int) -> dict:
    y_true = [lbl for _, lbl in held_out]
    eval_paths = [p for p, _ in held_out]

    # Majority class from the auto-labeled training pool (no eval leakage).
    majority = Counter(lbl for _, lbl in train_pool).most_common(1)[0][0]

    # Train ML model on the auto-labeled pool (production protocol).
    model = URLIntentModel()
    rng = random.Random(seed)
    train = list(train_pool)
    rng.shuffle(train)
    for path, label in train:
        model.train(path, label)

    baselines = {
        "majority": majority_predict(eval_paths, majority),
        "rule_only": rule_only_predict(eval_paths, model, majority),
        "ml_only": ml_only_predict(eval_paths, model),
        "hybrid": hybrid_predict(eval_paths, model),
    }

    classes = sorted(set(y_true) | set(CLASSES))
    results: dict = {
        "seed": seed,
        "n_train_pool": len(train_pool),
        "n_held_out": len(held_out),
        "majority_class": majority,
        "baselines": {},
    }

    for name, y_pred in baselines.items():
        metrics = evaluate(y_true, y_pred)
        matrix = confusion_matrix(y_true, y_pred, classes)
        correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
        lo, hi = wilson_ci(correct, len(y_true))
        results["baselines"][name] = {
            "accuracy": round(metrics["accuracy"], 4),
            "accuracy_ci95": [round(lo, 4), round(hi, 4)],
            "macro_f1": metrics["macro_f1"],
            "micro_f1": metrics["micro_f1"],
            "per_class": metrics["classes"],
            "confusion_matrix": matrix,
            "support": {c: metrics["classes"].get(c, {}).get("support", 0) for c in classes},
        }

    # Abstention only applies to ML-based baselines (detectors are deterministic).
    for name in ("ml_only", "hybrid"):
        uncertain = sum(1 for p in eval_paths if model.predict(p)["is_uncertain"])
        results["baselines"][name]["abstention"] = uncertain
        results["baselines"][name]["abstention_rate"] = round(uncertain / len(eval_paths), 4)

    results["classes"] = classes
    return results


def report(results: dict) -> None:
    classes = results["classes"]
    print("=" * 74)
    print(f"BASELINE BENCHMARK  (train_pool={results['n_train_pool']:,}, "
          f"held_out={results['n_held_out']}, seed={results['seed']})")
    print(f"majority class: {results['majority_class']}")
    print("=" * 74)

    print(f"\n{'baseline':<12} {'acc':>7} {'95% CI':>18} {'macro-F1':>9} {'abst':>6}")
    print("-" * 58)
    for name, b in results["baselines"].items():
        ci = f"[{b['accuracy_ci95'][0]:.3f},{b['accuracy_ci95'][1]:.3f}]"
        abst = b.get("abstention_rate", 0.0)
        print(f"{name:<12} {b['accuracy']:>7.4f} {ci:>18} {b['macro_f1']:>9.4f} {abst:>6.1%}")

    print("\nPer-class F1:")
    header = f"{'class':<14}" + "".join(f"{name[:10]:>12}" for name in results["baselines"])
    print(header)
    print("-" * len(header))
    for c in classes:
        row = f"{c:<14}"
        for name, b in results["baselines"].items():
            m = b["per_class"].get(c, {})
            row += f"{m.get('f1', 0.0):>12.4f}"
        print(row)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/paths.txt")
    parser.add_argument("--annotations", default="data/annotate/sample_labeled.csv")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--json-out", default="output/baseline_results.json")
    args = parser.parse_args()

    ann_path = PROJECT_ROOT / args.annotations
    in_path = PROJECT_ROOT / args.input
    if not ann_path.exists() or not in_path.exists():
        print("Error: annotations or input file not found.")
        return 2

    held_out = load_annotations(ann_path)
    if not held_out:
        print("Error: no labeled rows found.")
        return 2

    all_paths = load_paths(in_path)
    held_paths = {p for p, _ in held_out}
    train_paths = [p for p in all_paths if p not in held_paths]
    train_pool = auto_label_pool(train_paths)

    print(f"Train pool (auto-labeled): {len(train_pool):,}")
    print(f"Development-held-out (heuristic-assisted): {len(held_out)}")

    results = run_benchmark(held_out, train_pool, args.seed)
    report(results)

    out = PROJECT_ROOT / args.json_out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nWrote -> {args.json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
