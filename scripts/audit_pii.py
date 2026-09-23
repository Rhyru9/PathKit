#!/usr/bin/env python3
"""
audit_pii.py — Detect and report personally-identifiable information (PII)
in the PathKit dataset.

Uses scripts/pii_rules.py (canonical shared patterns) so it can never diverge
from the sanitizer. Emits data/audit/pii_report.json.

Usage:
    python scripts/audit_pii.py
"""

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pii_rules import RULES, decode

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA = PROJECT_ROOT / "data"
AUDIT = DATA / "audit"


def load_lines(path: Path) -> list[str]:
    with open(path, encoding="utf-8", errors="replace") as f:
        return [line.strip() for line in f if line.strip()]


def safe_sample(value: str, kind: str) -> str:
    """Avoid copying credentials or direct identifiers into logs/reports."""
    if kind == "credential":
        return "[REDACTED_CREDENTIAL]"
    if kind == "email":
        return "[REDACTED_EMAIL]"
    if kind == "phone":
        return "[REDACTED_PHONE]"
    if kind in {"id_code", "nip_name"}:
        return f"[REDACTED_{kind.upper()}]"
    if kind == "encoded_name":
        return "[REDACTED_ENCODED_NAME]"
    return value[:70]


def scan(paths: list[str]) -> dict:
    """Return per-type counts + sample list for a set of paths (decoded)."""
    counts = Counter()
    samples: dict[str, list[str]] = {}

    for p in paths:
        decoded = decode(p)
        for name, rx, _ in RULES:
            if rx.search(decoded):
                counts[name] += 1
                if len(samples.setdefault(name, [])) < 5:
                    samples[name].append(safe_sample(decoded, name))

    return {"counts": dict(counts), "samples": samples}


def main() -> int:
    AUDIT.mkdir(parents=True, exist_ok=True)

    paths = load_lines(DATA / "paths.txt")
    endpoints = load_lines(DATA / "endpoints.txt")

    report = {
        "files": {
            "paths.txt": {"size": len(paths), **scan(paths)},
            "endpoints.txt": {"size": len(endpoints), **scan(endpoints)},
        },
        "severity": {name: sev for name, _, sev in RULES},
        "assessment": {
            "pii_present": True,
            "recommendation": "redact or exclude before any public release",
            "law_ref": "UU PDP 2022 (personal data), UU KIP 2008 (public info)",
        },
    }

    (AUDIT / "pii_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print("=== PII AUDIT ===")
    for fname, data in report["files"].items():
        print(f"\n{fname} ({data['size']:,} rows):")
        for name, _, sev in RULES:
            c = data["counts"].get(name, 0)
            print(f"  {name:<14} {c:>7,}  ({sev})")
            for s in data["samples"].get(name, [])[:2]:
                print(f"      e.g. {s}")

    print("\nReport -> data/audit/pii_report.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
