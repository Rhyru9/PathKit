#!/usr/bin/env python3
"""
PathKit - URL Path Token Classifier

Usage:
    python main.py classify          # Full pipeline: train + classify + export
    python main.py slugs             # Run slug classifier pipeline
    python main.py detect <path>     # Classify a single path with all detectors
    python main.py scan              # Run all detectors over full dataset
    python main.py stats             # Print dataset statistics

Options:
    --input PATH     Path to paths.txt (default: data/paths.txt)
    --output DIR     Output directory (default: output/slugs)
    --weights PATH   Weights file path (default: weights/slugs_v4.json)
"""

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

from models.slugs import URLIntentModel
from models.slugs.pipeline import run as run_slugs

# ── CLI ────────────────────────────────────────────

_HELP_TEXT = (
    (__doc__ or "").split("Usage:")[1] if __doc__ and "Usage:" in __doc__ else ""
)

parser = argparse.ArgumentParser(
    description="PathKit - URL Path Token Classifier",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=_HELP_TEXT,
)
sub = parser.add_subparsers(dest="command", help="Commands")

# classify - full pipeline
p_cls = sub.add_parser(
    "classify", help="Full pipeline: train + classify + export slugs"
)
p_cls.add_argument("--input", default="data/paths.txt")
p_cls.add_argument("--output", default="output/slugs")
p_cls.add_argument("--weights", default="weights/slugs_v4.json")

# slugs - just the slug classifier
p_slugs = sub.add_parser("slugs", help="Run slug classifier pipeline")
p_slugs.add_argument("--input", default="data/paths.txt")
p_slugs.add_argument("--output", default="output/slugs")
p_slugs.add_argument("--weights", default="weights/slugs_v4.json")

# detect - single path
p_det = sub.add_parser("detect", help="Classify a single path with all detectors")
p_det.add_argument("path", help="URL path token to classify")

# scan - all detectors over full dataset
p_scan = sub.add_parser("scan", help="Run all identifier detectors over full dataset")
p_scan.add_argument("--input", default="data/paths.txt")

# stats - dataset statistics
p_stats = sub.add_parser("stats", help="Print dataset statistics")
p_stats.add_argument("--input", default="data/paths.txt")

args = parser.parse_args()

# ── Helpers ────────────────────────────────────────


def load_paths(txt_path: str) -> list[str]:
    """Load clean path tokens from a text file (one per line)."""
    p = Path(txt_path)
    if not p.exists():
        print(f"Error: file not found: {p}")
        print("Run: python main.py --help")
        sys.exit(1)
    with open(p, encoding="utf-8", errors="replace") as f:
        return [line.strip() for line in f if line.strip()]


def url_decode(raw: str) -> str:
    return re.sub(r"%([0-9A-Fa-f]{2})", lambda m: chr(int(m.group(1), 16)), raw.strip())


# ── Command: classify ──────────────────────────────


def cmd_classify(a):
    print("=" * 60)
    print("  PathKit - Full Classification Pipeline")
    print("=" * 60)
    run_slugs(
        paths_txt=a.input,
        output_dir=a.output,
        weights_file=a.weights,
    )


# ── Command: slugs ─────────────────────────────────


def cmd_slugs(a):
    cmd_classify(a)


# ── Command: detect ────────────────────────────────


def _try_import(module_name: str, fn_name: str):
    try:
        mod = __import__(module_name, fromlist=[fn_name])
        return getattr(mod, fn_name)
    except Exception:
        return None


def cmd_detect(a):
    raw = a.path
    decoded = url_decode(raw)

    print(f"\n  Path: {raw}")
    print(f"  Decoded: {decoded}\n")
    print(f"  {'DETECTOR':<12} {'SCORE':>6}  {'TYPE':<14}  {'-> CLASS'}")
    print(f"  {'-' * 50}")

    # UUID
    score_fn = _try_import("models.uuid", "score")
    if score_fn:
        s = score_fn(raw)
        t = _try_import("models.uuid", "detect")
        t_str = t(raw) if t else "-"
        label = "random_id" if s > 0.5 else "-"
        print(f"  {'uuid':<12} {s:>6.2f}  {t_str:<14}  -> {label}")

    # Timestamp
    score_fn = _try_import("models.timestamp", "score")
    if score_fn:
        s = score_fn(raw)
        t = _try_import("models.timestamp", "detect_type")
        t_str = t(raw) if t else "-"
        label = "api" if s > 0.7 else ("file" if s > 0.5 else "-")
        print(f"  {'timestamp':<12} {s:>6.2f}  {t_str:<14}  -> {label}")

    # Hash
    score_fn = _try_import("models.hash", "score")
    if score_fn:
        s = score_fn(raw)
        t = _try_import("models.hash", "detect_type")
        t_str = t(raw) if t else "-"
        label = "asset" if s > 0.5 else "-"
        print(f"  {'hash':<12} {s:>6.2f}  {t_str:<14}  -> {label}")

    # Base64
    score_fn = _try_import("models.base64", "score")
    if score_fn:
        s = score_fn(raw)
        t = _try_import("models.base64", "detect_type")
        t_str = t(raw) if t else "-"
        label = "api" if s > 0.5 else "-"
        print(f"  {'base64':<12} {s:>6.2f}  {t_str:<14}  -> {label}")

    # Other
    score_fn = _try_import("models.other", "score")
    if score_fn:
        s = score_fn(raw)
        t = _try_import("models.other", "detect_type")
        t_str = t(raw) if t else "-"
        label = "file" if s > 0.5 else "-"
        print(f"  {'other':<12} {s:>6.2f}  {t_str:<14}  -> {label}")

    # Slug classifier
    model = URLIntentModel()
    result = model.predict(raw)
    print(
        f"  {'slug':<12} {'-':>6}  {'-':<14}  -> {result['final']} (conf={result['confidence']:.3f})"
    )


# ── Command: scan ──────────────────────────────────


def cmd_scan(a):
    paths = load_paths(a.input)
    print(f"Loaded {len(paths):,} paths\n")

    detectors = {
        "uuid": _try_import("models.uuid", "score"),
        "timestamp": _try_import("models.timestamp", "score"),
        "hash": _try_import("models.hash", "score"),
        "base64": _try_import("models.base64", "score"),
        "other": _try_import("models.other", "score"),
    }
    detectors = {k: v for k, v in detectors.items() if v}

    counters = {name: Counter() for name in detectors}
    total_hits: Counter[str] = Counter()

    for raw in paths:
        for name, score_fn in detectors.items():
            s = score_fn(raw)
            if s > 0.5:
                total_hits[name] += 1
            if s > 0.7:
                counters[name]["high"] += 1
            elif s > 0.5:
                counters[name]["medium"] += 1

    print(f"  {'DETECTOR':<12} {'HITS':>8}  {'%':>6}  {'HIGH':>6}  {'MED':>6}")
    print(f"  {'-' * 48}")
    for name in detectors:
        hits = total_hits[name]
        pct = hits / len(paths) * 100
        high = counters[name]["high"]
        med = counters[name]["medium"]
        print(f"  {name:<12} {hits:>8,}  {pct:>5.1f}%  {high:>6,}  {med:>6,}")

    total = sum(total_hits.values())
    print(
        f"\n  Total paths with identifier signals: {total:,} / {len(paths):,} "
        f"({total / len(paths) * 100:.1f}%)"
    )


# ── Command: stats ─────────────────────────────────


def cmd_stats(a):
    paths = load_paths(a.input)
    print(f"Total paths: {len(paths):,}\n")

    lengths = [len(p) for p in paths]
    print(
        f"  Length: min={min(lengths)}  max={max(lengths)}  "
        f"avg={sum(lengths) / len(lengths):.1f}"
    )

    encoded = sum(1 for p in paths if "%" in p)
    print(f"  Percent-encoded: {encoded:,} ({encoded / len(paths) * 100:.1f}%)")

    dashed = sum(1 for p in paths if "-" in p)
    print(f"  Has dash: {dashed:,} ({dashed / len(paths) * 100:.1f}%)")

    dotted = sum(1 for p in paths if "." in p)
    print(f"  Has dot: {dotted:,} ({dotted / len(paths) * 100:.1f}%)")

    underscore = sum(1 for p in paths if "_" in p)
    print(f"  Has underscore: {underscore:,} ({underscore / len(paths) * 100:.1f}%)")

    digits = sum(1 for p in paths if p.isdigit())
    print(f"  Pure digits: {digits:,} ({digits / len(paths) * 100:.1f}%)")

    short = sum(1 for p in paths if len(p) < 20)
    print(f"  Short (<20 chars): {short:,} ({short / len(paths) * 100:.1f}%)")


# ── Dispatch ───────────────────────────────────────

if args.command == "classify":
    cmd_classify(args)
elif args.command == "slugs":
    cmd_slugs(args)
elif args.command == "detect":
    cmd_detect(args)
elif args.command == "scan":
    cmd_scan(args)
elif args.command == "stats":
    cmd_stats(args)
else:
    parser.print_help()
