#!/usr/bin/env python3
"""
uuid/runner.py - Run UUID analysis over all paths and export results.

Outputs (-> researchs/uuid/output/):
    standalone.txt      - standalone UUIDs (pure random_id)
    embedded.txt        - UUIDs embedded in text (CMS hybrid, needs review)
    asset.txt           - UUID + file extension (CDN assets)
    analysis.json       - full analysis for every UUID hit {raw: {score, context, ...}}
    summary.json        - distribution stats
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

# Allow running from project root or uuid/
sys.path.insert(0, str(Path(__file__).resolve().parent))
from detector import CONTEXT_TO_CLASS, UUIDContext, analyze

OUT = Path(__file__).resolve().parent / "output"
OUT.mkdir(parents=True, exist_ok=True)

# ── Load paths (same loader as pipeline) ──────────


def load_paths(txt_path: str) -> list[str]:
    """Load clean path tokens from a text file (one per line)."""
    project_root = Path(__file__).resolve().parent.parent.parent
    path = project_root / txt_path
    with open(path, encoding="utf-8", errors="replace") as f:
        return [line.strip() for line in f if line.strip()]


# ── Decode helper ────────────────────────────────


def url_decode(raw: str) -> str:
    return re.sub(
        r"%([0-9A-Fa-f]{2})",
        lambda m: chr(int(m.group(1), 16)),
        raw.strip(),
    )


# ── Run ──────────────────────────────────────────


def main():
    print("UUID Research - Full Analysis")
    print("=" * 60)

    paths = load_paths("data/paths.txt")
    print(f"Loaded {len(paths):,} paths")

    # Scan
    buckets: dict[UUIDContext, list[tuple[str, dict]]] = {
        UUIDContext.STANDALONE: [],
        UUIDContext.EMBEDDED: [],
        UUIDContext.ASSET: [],
        UUIDContext.QUERY: [],
    }
    results: dict[str, dict] = {}
    ctx_counter: Counter = Counter()

    for raw in paths:
        a = analyze(raw)
        ctx = UUIDContext(a["uuid_context"])
        if ctx == UUIDContext.NONE:
            continue
        ctx_counter[ctx.value] += 1
        a["decoded"] = url_decode(raw)[:120]
        results[raw] = a
        if ctx in buckets:
            buckets[ctx].append((raw, a))

    total_hits = sum(ctx_counter.values())
    print(
        f"UUID hits: {total_hits:,} / {len(paths):,} ({total_hits / len(paths) * 100:.1f}%)\n"
    )

    # ── Write per-context files ──────────────────

    for ctx in (
        UUIDContext.STANDALONE,
        UUIDContext.EMBEDDED,
        UUIDContext.ASSET,
        UUIDContext.QUERY,
    ):
        fname = f"{ctx.value}.txt"
        lines = [raw for raw, _ in buckets[ctx]]
        (OUT / fname).write_text("\n".join(lines), encoding="utf-8")
        top = [url_decode(raw)[:60] for raw, _ in buckets[ctx][:5]]
        print(f"  {fname:<18} {len(lines):>6,}  samples: {top}")

    # ── Write JSON outputs ───────────────────────

    (OUT / "analysis.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    summary = {
        "total_paths": len(paths),
        "uuid_hits": total_hits,
        "hit_pct": round(total_hits / len(paths) * 100, 2),
        "distribution": dict(ctx_counter),
        "mapping": {k.value: v for k, v in CONTEXT_TO_CLASS.items()},
    }
    (OUT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # ── Stats ────────────────────────────────────

    scores = [r["uuid_score"] for r in results.values()]
    print(
        f"\n  Score range: {min(scores):.2f} - {max(scores):.2f}  avg: {sum(scores) / len(scores):.3f}"
    )

    uniform = sum(1 for r in results.values() if r["is_hex_uniform"])
    isolated = sum(1 for r in results.values() if r["is_semantically_isolated"])
    print(f"  Hex-uniform: {uniform}  Semantically-isolated: {isolated}")

    print("\nresearchs/uuid/output/")
    for f in sorted(OUT.iterdir()):
        if f.is_file():
            print(f"  {f.name:<25} {f.stat().st_size:>10,} bytes")


if __name__ == "__main__":
    main()
