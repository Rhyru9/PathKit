#!/usr/bin/env python3
"""
other/runner.py - Run "other" (catch-all) analysis over all paths.

Outputs (-> researchs/other/output/):
    org_unit.txt      - org unit codes (ditjen=5F...)
    dotted_version.txt - dotted version paths (PED003.3.4)
    numeric_id.txt    - short pure numeric IDs
    analysis.json     - full metadata
    summary.json      - distribution stats
"""

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from detector import analyze

OUT = Path(__file__).resolve().parent / "output"
OUT.mkdir(parents=True, exist_ok=True)


def load_paths(txt_path: str) -> list[str]:
    """Load clean path tokens from a text file (one per line)."""
    project_root = Path(__file__).resolve().parent.parent.parent
    path = project_root / txt_path
    with open(path, encoding="utf-8", errors="replace") as f:
        return [line.strip() for line in f if line.strip()]


def main():
    print("Other Research - Full Analysis")
    print("=" * 60)

    paths = load_paths("data/paths.txt")
    print(f"Loaded {len(paths):,} paths\n")

    buckets: dict[str, list[str]] = {
        "org_unit": [],
        "dotted_version": [],
        "numeric_id": [],
    }
    results: dict[str, dict] = {}
    type_counter: Counter = Counter()
    artifact_count = 0

    for raw in paths:
        a = analyze(raw)
        bt = a["other_type"]
        if bt == "none":
            continue

        results[raw] = a
        type_counter[bt] += 1
        if a["is_system_artifact"]:
            artifact_count += 1
        if bt in buckets:
            buckets[bt].append(raw)

    total_hits = sum(type_counter.values())
    print(
        f"Other hits: {total_hits:,} / {len(paths):,} ({total_hits / len(paths) * 100:.1f}%)"
    )
    print(f"System artifacts (all detectors): {artifact_count:,}\n")

    for bt, lines in buckets.items():
        fname = f"{bt}.txt"
        (OUT / fname).write_text("\n".join(lines), encoding="utf-8")
        print(f"  {fname:<20} {len(lines):>8,}  samples: {lines[:3]}")

    (OUT / "analysis.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    summary = {
        "total_paths": len(paths),
        "other_hits": total_hits,
        "hit_pct": round(total_hits / len(paths) * 100, 2),
        "distribution": dict(type_counter),
        "system_artifacts_total": artifact_count,
    }
    (OUT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("\nresearchs/other/output/")
    for f in sorted(OUT.iterdir()):
        if f.is_file():
            print(f"  {f.name:<25} {f.stat().st_size:>10,} bytes")


if __name__ == "__main__":
    main()
