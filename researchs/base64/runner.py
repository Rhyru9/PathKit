#!/usr/bin/env python3
"""
base64/runner.py - Run base64 analysis over all paths.

Outputs (-> researchs/base64/output/):
    jwt.txt         - JWT/Laravel encrypted tokens
    classic.txt     - classic Base64 (mixed case)
    urlsafe.txt     - URL-safe Base64
    analysis.json   - full metadata
    summary.json    - distribution stats
"""

import json
import re
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


def url_decode(raw: str) -> str:
    return re.sub(r"%([0-9A-Fa-f]{2})", lambda m: chr(int(m.group(1), 16)), raw.strip())


def main():
    print("Base64 Research - Full Analysis")
    print("=" * 60)

    paths = load_paths("data/paths.txt")
    print(f"Loaded {len(paths):,} paths\n")

    buckets: dict[str, list[str]] = {"jwt": [], "classic": []}
    results: dict[str, dict] = {}
    type_counter: Counter = Counter()
    hint_counter: Counter = Counter()

    for raw in paths:
        a = analyze(raw)
        bt = a["base64_type"]
        if bt == "none":
            continue

        a["decoded"] = url_decode(raw)[:120]
        results[raw] = a
        type_counter[bt] += 1
        if hint := a["classification_hint"]:
            hint_counter[hint] += 1
        if bt in buckets:
            buckets[bt].append(raw)

    total_hits = sum(type_counter.values())
    print(
        f"Base64 hits: {total_hits:,} / {len(paths):,} ({total_hits / len(paths) * 100:.1f}%)\n"
    )

    for bt, lines in buckets.items():
        fname = f"{bt}.txt"
        (OUT / fname).write_text("\n".join(lines), encoding="utf-8")
        samples = [url_decode(r)[:60] for r in lines[:3]]
        print(f"  {fname:<12} {len(lines):>6,}  samples: {samples}")

    (OUT / "analysis.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    scores = [r["base64_score"] for r in results.values()]
    summary = {
        "total_paths": len(paths),
        "base64_hits": total_hits,
        "hit_pct": round(total_hits / len(paths) * 100, 2),
        "distribution": dict(type_counter),
        "classification_hints": dict(hint_counter),
        "score_range": {"min": min(scores), "max": max(scores)},
    }
    (OUT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"\n  Hints: {dict(hint_counter)}")
    print(f"  Score: {min(scores):.2f} - {max(scores):.2f}")

    print("\nresearchs/base64/output/")
    for f in sorted(OUT.iterdir()):
        if f.is_file():
            print(f"  {f.name:<20} {f.stat().st_size:>10,} bytes")


if __name__ == "__main__":
    main()
