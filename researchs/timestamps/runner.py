#!/usr/bin/env python3
"""
timestamps/runner.py - Run timestamp analysis over all paths and export results.

Outputs (-> researchs/timestamps/output/):
    unix_s.txt        - unix second timestamps
    unix_ms.txt        - unix millisecond timestamps
    iso_date.txt       - ISO date strings
    iso_datetime.txt   - ISO datetime strings
    date_path.txt      - date-path patterns (/YYYY/MM/DD/)
    hybrid_slug.txt    - date path + readable words (CMS hybrid)
    analysis.json      - full analysis for every timestamp hit
    summary.json       - distribution stats
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from detector import TimestampType, analyze

OUT = Path(__file__).resolve().parent / "output"
OUT.mkdir(parents=True, exist_ok=True)


def load_paths(txt_path: str) -> list[str]:
    """Load clean path tokens from a text file (one per line)."""
    project_root = Path(__file__).resolve().parent.parent.parent
    path = project_root / txt_path
    with open(path, encoding="utf-8", errors="replace") as f:
        return [line.strip() for line in f if line.strip()]


def url_decode(raw: str) -> str:
    return re.sub(
        r"%([0-9A-Fa-f]{2})",
        lambda m: chr(int(m.group(1), 16)),
        raw.strip(),
    )


def main():
    print("Timestamp Research - Full Analysis")
    print("=" * 60)

    paths = load_paths("data/paths.txt")
    print(f"Loaded {len(paths):,} paths\n")

    # ── Scan ──────────────────────────────────────

    buckets: dict[TimestampType, list[str]] = {
        TimestampType.UNIX_S: [],
        TimestampType.UNIX_MS: [],
        TimestampType.ISO_DATE: [],
        TimestampType.ISO_DATETIME: [],
        TimestampType.DATE_PATH: [],
    }
    hybrid_slugs: list[str] = []
    results: dict[str, dict] = {}
    type_counter: Counter = Counter()
    hint_counter: Counter = Counter()

    for raw in paths:
        a = analyze(raw)
        if not a["has_timestamp"]:
            continue

        ts_type = TimestampType(a["timestamp_type"])
        a["decoded"] = url_decode(raw)[:120]
        results[raw] = a

        type_counter[ts_type.value] += 1
        if hint := a["classification_hint"]:
            hint_counter[hint] += 1

        if ts_type in buckets:
            buckets[ts_type].append(raw)
        if a["is_hybrid_slug"]:
            hybrid_slugs.append(raw)

    total_hits = sum(type_counter.values())
    print(
        f"Timestamp hits: {total_hits:,} / {len(paths):,} "
        f"({total_hits / len(paths) * 100:.1f}%)\n"
    )

    # ── Write per-type files ──────────────────────

    for ts_type, lines in buckets.items():
        fname = f"{ts_type.value}.txt"
        (OUT / fname).write_text("\n".join(lines), encoding="utf-8")
        samples = [url_decode(r)[:60] for r in lines[:3]]
        print(f"  {fname:<18} {len(lines):>7,}  samples: {samples}")

    (OUT / "hybrid_slug.txt").write_text("\n".join(hybrid_slugs), encoding="utf-8")
    print(
        f"  hybrid_slug.txt    {len(hybrid_slugs):>7,}  "
        f"samples: {[url_decode(r)[:50] for r in hybrid_slugs[:3]]}"
    )

    # ── JSON outputs ──────────────────────────────

    (OUT / "analysis.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    scores = [r["timestamp_score"] for r in results.values()]
    summary = {
        "total_paths": len(paths),
        "timestamp_hits": total_hits,
        "hit_pct": round(total_hits / len(paths) * 100, 2),
        "distribution": dict(type_counter),
        "classification_hints": dict(hint_counter),
        "score_range": {"min": min(scores), "max": max(scores)},
        "hybrid_slugs": len(hybrid_slugs),
    }
    (OUT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # ── Stats ────────────────────────────────────

    print("\n  Classification hints:")
    for hint, cnt in hint_counter.most_common():
        print(f"    {hint}: {cnt:,}")

    avg = sum(scores) / len(scores)
    print(f"  Score range: {min(scores):.2f} - {max(scores):.2f}  avg: {avg:.3f}")

    print("\nresearchs/timestamps/output/")
    for f in sorted(OUT.iterdir()):
        if f.is_file():
            sz = f.stat().st_size
            print(f"  {f.name:<25} {sz:>10,} bytes")


if __name__ == "__main__":
    main()
