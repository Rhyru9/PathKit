"""
supervised_baselines.py — Independent supervised baselines (TF-IDF + Logistic
Regression, and a Decision Tree) compared against PathKit's baselines.

Requires scikit-learn (dev dependency, not part of the stdlib-only core).

Trains each supervised model on the SAME auto-labeled pool and evaluates on the
SAME 500-row development-held-out split as eval/baselines.py, so all numbers
are directly comparable.

Usage (needs a Python with scikit-learn):
    python eval/supervised_baselines.py [--seed 42] [--json-out ...]
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from eval.baselines import auto_label_pool, load_paths
from eval.harness import confusion_matrix, evaluate, load_annotations

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.pipeline import make_pipeline
except ImportError as e:  # pragma: no cover
    print(f"scikit-learn required: {e}")
    print("Install with: python -m pip install scikit-learn")
    raise SystemExit(2)


def char_ngrams(path: str) -> str:
    """Return a space-joined char n-gram representation (2-4 grams)."""
    from urllib.parse import unquote
    s = unquote(path, errors="replace").lower()
    # boundaries for n-gram splitting
    out = []
    for n in (2, 3, 4):
        for i in range(len(s) - n + 1):
            out.append(s[i:i + n])
    return " ".join(out)


def build_models(train_paths: list[str], train_labels: list[str]):
    """Build TF-IDF + LR and Decision Tree pipelines."""
    tfidf = TfidfVectorizer(analyzer="word", lowercase=True, ngram_range=(1, 1),
                            max_features=5000, sublinear_tf=True)
    lr = make_pipeline(tfidf, LogisticRegression(max_iter=1000, class_weight="balanced"))
    dt = make_pipeline(tfidf, DecisionTreeClassifier(max_depth=10, class_weight="balanced"))

    X = [char_ngrams(p) for p in train_paths]
    lr.fit(X, train_labels)
    dt.fit(X, train_labels)
    return lr, dt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/paths.txt")
    parser.add_argument("--annotations", default="data/annotate/sample_labeled.csv")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--json-out", default="output/supervised_baseline_results.json")
    args = parser.parse_args()

    ann_path = PROJECT_ROOT / args.annotations
    in_path = PROJECT_ROOT / args.input
    held_out = load_annotations(ann_path)
    all_paths = load_paths(in_path)
    held_paths = {p for p, _ in held_out}
    train_pool = auto_label_pool([p for p in all_paths if p not in held_paths])

    train_paths = [p for p, _ in train_pool]
    train_labels = [l for _, l in train_pool]
    eval_paths = [p for p, _ in held_out]
    y_true = [l for _, l in held_out]

    print(f"Train pool: {len(train_pool):,}  Held-out: {len(held_out)}")

    # Build supervised models (with runtime).
    results: dict = {"seed": args.seed, "baselines": {}}

    t0 = time.time()
    lr, dt = build_models(train_paths, train_labels)
    build_time = time.time() - t0

    for name, clf in (("tfidf_lr", lr), ("decision_tree", dt)):
        t0 = time.time()
        y_pred = clf.predict([char_ngrams(p) for p in eval_paths])
        infer_time = time.time() - t0
        metrics = evaluate(y_true, list(y_pred))
        classes = sorted(set(y_true) | set(y_pred))
        matrix = confusion_matrix(y_true, list(y_pred), classes)
        results["baselines"][name] = {
            "accuracy": metrics["accuracy"],
            "macro_f1": metrics["macro_f1"],
            "per_class": metrics["classes"],
            "confusion_matrix": matrix,
            "runtime_build_s": round(build_time / 2, 4),
            "runtime_infer_s": round(infer_time, 4),
        }

    results["classes"] = classes

    print("=" * 60)
    print("SUPERVISED BASELINES (TF-IDF + LR, Decision Tree)")
    print("=" * 60)
    print(f"\n{'baseline':<16} {'acc':>7} {'macro-F1':>9} {'infer_s':>9}")
    print("-" * 46)
    for name, b in results["baselines"].items():
        print(f"{name:<16} {b['accuracy']:>7.4f} {b['macro_f1']:>9.4f} "
              f"{b['runtime_infer_s']:>9.4f}")

    print(f"\nPer-class F1:")
    header = f"{'class':<14}" + "".join(f"{n[:12]:>14}" for n in results["baselines"])
    print(header)
    for c in classes:
        row = f"{c:<14}"
        for name in results["baselines"]:
            m = results["baselines"][name]["per_class"].get(c, {})
            row += f"{m.get('f1', 0.0):>14.4f}"
        print(row)

    out = PROJECT_ROOT / args.json_out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nWrote -> {args.json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
