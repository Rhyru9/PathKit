#!/usr/bin/env python3
"""
hash/runner.py - Run hash analysis over all paths and export results.

Outputs (-> researchs/hash/output/):
    md5.txt           - MD5 hashes
    sha1.txt          - SHA1 hashes
    sha256.txt        - SHA256 hashes
    truncated.txt     - truncated hex (8-16)
    generic.txt       - generic long hex (24+)
    bundler_chunk.txt - bundler artifacts (name-<hash>.js)
    embedded.txt      - hash+words (CMS hybrid)
    analysis.json     - full metadata
    summary.json      - distribution stats
    identifier_scores.json - uuid/timestamp/hash comparison for all hits
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from detector import analyze, identifier_type_scores

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
    print("Hash Research - Full Analysis")
    print("=" * 60)

    paths = load_paths("data/paths.txt")
    print(f"Loaded {len(paths):,} paths\n")

    # ── Scan ──────────────────────────────────────

    type_buckets: dict[str, list[str]] = {
        "md5": [],
        "sha1": [],
        "sha256": [],
        "truncated": [],
        "generic": [],
    }
    bundler_chunks: list[str] = []
    embedded_hashes: list[str] = []
    results: dict[str, dict] = {}
    id_scores: dict[str, dict] = {}
    type_counter: Counter = Counter()
    hint_counter: Counter = Counter()

    for raw in paths:
        a = analyze(raw)
        htype = a["hash_type"]
        if htype == "none":
            continue

        a["decoded"] = url_decode(raw)[:120]
        results[raw] = a
        id_scores[raw] = identifier_type_scores(raw)

        type_counter[htype] += 1
        if hint := a["classification_hint"]:
            hint_counter[hint] += 1

        if htype in type_buckets:
            type_buckets[htype].append(raw)
        if a["is_bundler_chunk"]:
            bundler_chunks.append(raw)
        if a["is_hash_embedded"]:
            embedded_hashes.append(raw)

    total_hits = sum(type_counter.values())
    print(
        f"Hash hits: {total_hits:,} / {len(paths):,} "
        f"({total_hits / len(paths) * 100:.1f}%)\n"
    )

    # ── Write per-type files ──────────────────────

    for htype, lines in type_buckets.items():
        fname = f"{htype}.txt"
        (OUT / fname).write_text("\n".join(lines), encoding="utf-8")
        samples = [url_decode(r)[:55] for r in lines[:3]]
        print(f"  {fname:<16} {len(lines):>8,}  samples: {samples}")

    (OUT / "bundler_chunk.txt").write_text("\n".join(bundler_chunks), encoding="utf-8")
    (OUT / "embedded.txt").write_text("\n".join(embedded_hashes), encoding="utf-8")
    print(f"  bundler_chunk.txt {len(bundler_chunks):>8,}")
    print(f"  embedded.txt     {len(embedded_hashes):>8,}  (CMS hybrid)\n")

    # ── JSON outputs ──────────────────────────────

    (OUT / "analysis.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUT / "identifier_scores.json").write_text(
        json.dumps(id_scores, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    scores = [r["hash_score"] for r in results.values()]
    summary = {
        "total_paths": len(paths),
        "hash_hits": total_hits,
        "hit_pct": round(total_hits / len(paths) * 100, 2),
        "distribution": dict(type_counter),
        "classification_hints": dict(hint_counter),
        "bundler_chunks": len(bundler_chunks),
        "embedded_hashes": len(embedded_hashes),
        "score_range": {"min": min(scores), "max": max(scores)},
    }
    (OUT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # ── Stats ────────────────────────────────────

    print("  Classification hints:")
    for hint, cnt in hint_counter.most_common():
        print(f"    {hint}: {cnt:,}")

    avg = sum(scores) / len(scores)
    print(f"  Score range: {min(scores):.2f} - {max(scores):.2f}  avg: {avg:.3f}")

    print("\nresearchs/hash/output/")
    for f in sorted(OUT.iterdir()):
        if f.is_file():
            sz = f.stat().st_size
            print(f"  {f.name:<25} {sz:>10,} bytes")


if __name__ == "__main__":
    main()
