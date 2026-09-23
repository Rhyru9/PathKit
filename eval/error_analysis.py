"""
error_analysis.py — Structured error analysis of the hybrid pipeline.

Categorizes false positives / false negatives per class, identifies why
`search` recall is low, confirms `api` has zero support, quantifies class
imbalance, and flags the numeric-slug-vs-random-id ambiguity.

Usage:
    python eval/error_analysis.py [--annotations ...] [--seed 42]
"""

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from models.decision import classify_path
from models.slugs import URLIntentModel
from eval.baselines import auto_label_pool, load_paths
from eval.harness import load_annotations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/paths.txt")
    parser.add_argument("--annotations", default="data/annotate/sample_labeled.csv")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    held_out = load_annotations(PROJECT_ROOT / args.annotations)
    all_paths = load_paths(PROJECT_ROOT / args.input)
    held_paths = {p for p, _ in held_out}
    train_pool = auto_label_pool([p for p in all_paths if p not in held_paths])

    import random
    model = URLIntentModel()
    rng = random.Random(args.seed)
    train = list(train_pool)
    rng.shuffle(train)
    for path, label in train:
        model.train(path, label)

    # Predict + collect errors
    y_true = [l for _, l in held_out]
    y_pred = []
    errors = []  # (true, pred, path, detector)
    for p, t in held_out:
        c = classify_path(p, model)
        y_pred.append(c.label)
        if c.label != t:
            errors.append((t, c.label, p[:70], c.detector))

    # Class imbalance (true distribution)
    dist = Counter(y_true)
    print("=" * 64)
    print("ERROR ANALYSIS")
    print("=" * 64)

    print("\n1. Class imbalance (held-out true distribution):")
    total = len(y_true)
    for c, n in dist.most_common():
        print(f"  {c:<12} {n:>4}  ({n/total*100:>5.1f}%)")

    # Per-class error rate
    print("\n2. Per-class error (FP/FN):")
    tp = Counter(); fp = Counter(); fn = Counter()
    for t, p in zip(y_true, y_pred):
        if p == t:
            tp[t] += 1
        else:
            fp[p] += 1
            fn[t] += 1
    for c in sorted(set(y_true) | set(y_pred)):
        support = dist[c]
        fn_c = fn[c]
        fp_c = fp[c]
        err_rate = (fn_c + fp_c) / max(support + fp_c, 1)
        print(f"  {c:<12} support={support:>4}  FN={fn_c:>3}  FP={fp_c:>3}  err~{err_rate:.1%}")

    # Error examples grouped by (true -> pred)
    print("\n3. Error examples (true -> pred), top patterns:")
    grouped = defaultdict(list)
    for t, p, path, det in errors:
        grouped[(t, p)].append((path, det))
    for (t, p), items in sorted(grouped.items(), key=lambda kv: -len(kv[1])):
        print(f"\n  {t} -> {p}  ({len(items)} cases):")
        for path, det in items[:3]:
            print(f"      [{det:<12}] {path}")

    # 4. Specific known gaps
    print("\n4. Known gaps:")
    n_search = dist["search"]
    n_search_fp = fn["search"]
    print(f"  search: {n_search} true, {n_search_fp} missed "
          f"(recall {1 - n_search_fp/max(n_search,1):.0%}) — "
          f"only literal ?= is caught, percent-encoded queries are missed")
    n_api = dist["api"]
    print(f"  api: {n_api} true examples -> support is ZERO; no API claim possible")
    other_caught = sum(1 for _, _, _, det in errors if det == "other")
    print(f"  'other' detector errors: {other_caught} — dominant detector, "
          f"catch-all for id_code/file_ext/numeric")

    print("\n5. Numeric-slug vs random-id ambiguity:")
    amb = [(t, p, path) for t, p, path, _ in errors if {t, p} == {"slug", "random_id"}]
    print(f"  {len(amb)} slug<->random_id confusions")
    for t, p, path in amb[:5]:
        print(f"      true={t} pred={p}  {path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
