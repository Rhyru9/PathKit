"""
pipeline.py - End-to-end training, classification, and export of slug paths.
"""

import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

from .classifier import URLIntentModel
from .labeling import auto_label


def _url_decode(raw: str) -> str:
    return re.sub(
        r"%([0-9A-Fa-f]{2})",
        lambda m: chr(int(m.group(1), 16)),
        raw.strip(),
    )


def load_paths(path: str) -> list[str]:
    """Load clean path tokens from a text file (one per line)."""
    with open(path, encoding="utf-8", errors="replace") as f:
        return [line.strip() for line in f if line.strip()]


def build_training_set(paths: list[str]) -> list[tuple[str, str]]:
    """Auto-label paths and add negative examples for non-slugs."""
    train_data: list[tuple[str, str]] = []

    for raw in paths:
        label = auto_label(raw)
        if label:
            train_data.append((raw, label))
            continue

        s = _url_decode(raw).lower()
        if re.match(r"^[0-9a-f]{8}-", s):
            train_data.append((raw, "random_id"))
        elif "-" not in s and len(s) < 15 and not s.isalpha():
            train_data.append((raw, "file"))

    return train_data


def run(
    paths_txt: str = "data/paths.txt",
    output_dir: str = "output/slugs",
    weights_file: str = "weights/slugs_v4.json",
) -> URLIntentModel:
    """
    Full pipeline: load -> label -> train -> classify -> export slugs.

    Outputs (all placed under output_dir):
        slugs.txt          - high-confidence slug paths
        slugs_review.txt   - low-confidence slugs needing review
        slugs_with_conf.json - {raw_path: {confidence, decoded, tokens}} for all slugs
        summary.json       - classification distribution & stats
    Returns the trained model.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    paths = load_paths(paths_txt)
    print(f"Loaded {len(paths)} paths")

    # ── Auto-label ──
    print("Auto-labeling...")
    train_data = build_training_set(paths)
    print(f"Labeled: {len(train_data)}")
    for cls, cnt in Counter(label for _, label in train_data).most_common():
        print(f"  {cls}: {cnt}")

    # ── Train ──
    model = URLIntentModel()
    random.shuffle(train_data)
    split = int(len(train_data) * 0.8)
    train_set = train_data[:split]

    print(f"\nTraining on {len(train_set)} entries...")
    for raw, label in train_set:
        model.train(raw, label)

    # ── Classify ──
    print(f"Classifying {len(paths)} paths...\n")
    results: Counter[str] = Counter()
    samples: dict[str, list] = defaultdict(list)
    uncertain_count = 0

    for raw in paths:
        r = model.predict(raw)
        cls = r["final"]
        results[cls] += 1
        if r["is_uncertain"]:
            uncertain_count += 1
        if len(samples[cls]) < 5:
            samples[cls].append((raw[:60], r["confidence"]))

    total = sum(results.values())
    print(f"{'CLASS':<15} {'COUNT':>7}  {'%':>6}  {'CONF':>6}  SAMPLES")
    print("-" * 70)
    for cls in model.classes:
        cnt = results[cls]
        pct = cnt / max(total, 1) * 100
        confs = [c for _, c in samples[cls]]
        avg_conf = sum(confs) / max(len(confs), 1) if confs else 0
        sample = samples[cls][0][0][:50] if samples[cls] else ""
        print(f"{cls:<15} {cnt:>7}  {pct:>5.1f}%  {avg_conf:>5.3f}  {sample}")

    print(
        f"\nUncertain predictions: {uncertain_count}/{total} "
        f"({uncertain_count / max(total, 1) * 100:.1f}%)"
    )

    # Save model weights
    Path(weights_file).parent.mkdir(parents=True, exist_ok=True)
    model.save(weights_file)
    print(f"\nSaved {weights_file}")

    # ── Export slugs ──
    slug_paths: list[str] = []
    review_paths: list[tuple[str, dict]] = []
    slug_meta: dict[str, dict] = {}

    for raw in paths:
        r = model.predict(raw)
        s = _url_decode(raw).lower()

        if r["final"] != "slug":
            continue

        # Post-filters
        if not re.search(r"[-_]", s):
            continue
        if s.endswith("-") or s.startswith("-"):
            continue
        if "__trashed" in s:
            continue
        if re.search(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", s
        ):
            continue

        meta = {
            "decoded": s[:120],
            "confidence": round(r["confidence"], 4),
            "is_uncertain": r["is_uncertain"],
        }
        slug_meta[raw] = meta

        if r["is_uncertain"]:
            review_paths.append((raw, r))
        else:
            slug_paths.append(raw)

    # Write slugs.txt
    (out / "slugs.txt").write_text("\n".join(slug_paths), encoding="utf-8")

    # Write slugs_review.txt
    review_lines = [raw for raw, _ in review_paths]
    (out / "slugs_review.txt").write_text("\n".join(review_lines), encoding="utf-8")

    # Write slugs_with_conf.json (full metadata)
    (out / "slugs_with_conf.json").write_text(
        json.dumps(slug_meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Write summary.json
    summary = {
        "total_paths": total,
        "distribution": {cls: results[cls] for cls in model.classes},
        "uncertain_predictions": uncertain_count,
        "uncertain_pct": round(uncertain_count / max(total, 1) * 100, 2),
        "slugs_exported": len(slug_paths),
        "slugs_review": len(review_paths),
    }
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\n{output_dir}/")
    print(f"  slugs.txt             - {len(slug_paths)} high-confidence slugs")
    print(f"  slugs_review.txt      - {len(review_paths)} slugs for review")
    print("  slugs_with_conf.json  - metadata for all slugs")
    print("  summary.json          - classification stats")

    return model
