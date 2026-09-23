#!/usr/bin/env python3
"""
sanitize_dataset.py — Produce a PII-redacted (T1) copy of the dataset.

Uses scripts/pii_rules.py (canonical shared patterns). After redaction it
automatically RE-AUDITS the output and fails (exit 1) if any credential,
email, phone, or ID code survives.

Writes:
    data/sanitized/paths_clean.txt
    data/sanitized/endpoints_clean.txt
    data/sanitized/redaction_report.json

Never touches the originals.

Usage:
    python scripts/sanitize_dataset.py
"""

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pii_rules import decode, detect_all, redact_token

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA = PROJECT_ROOT / "data"
OUT = DATA / "sanitized"

# PII types that MUST NOT survive sanitization (re-audit gate).
MUST_BE_ZERO = {"credential", "email", "phone", "id_code", "nip_name"}


def process(lines: list[str]) -> tuple[list[str], Counter]:
    clean: list[str] = []
    redacted: Counter = Counter()
    for line in lines:
        out, label = redact_token(line)
        if label:
            redacted[label] += 1
        if out:
            clean.append(out)
    return clean, redacted


def re_audit(clean: list[str], source: str) -> Counter:
    """Detect surviving PII in the sanitized output."""
    leftover: Counter = Counter()
    for line in clean:
        for name in detect_all(decode(line)):
            leftover[name] += 1
    return leftover


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    paths = (DATA / "paths.txt").read_text(encoding="utf-8", errors="replace").splitlines()
    endpoints = (DATA / "endpoints.txt").read_text(encoding="utf-8", errors="replace").splitlines()

    clean_paths, rp = process([p.strip() for p in paths if p.strip()])
    clean_endpoints, re_ = process([e.strip() for e in endpoints if e.strip()])

    (OUT / "paths_clean.txt").write_text("\n".join(clean_paths) + "\n", encoding="utf-8")
    (OUT / "endpoints_clean.txt").write_text("\n".join(clean_endpoints) + "\n", encoding="utf-8")

    # ── Post-sanitization re-audit (fail if sensitive PII survives) ──
    leftover_paths = re_audit(clean_paths, "paths")
    leftover_endpoints = re_audit(clean_endpoints, "endpoints")

    report = {
        "paths.txt": {"before": len(paths), "after": len(clean_paths), "redacted": dict(rp)},
        "endpoints.txt": {"before": len(endpoints), "after": len(clean_endpoints), "redacted": dict(re_)},
        "re_audit": {
            "paths_clean.txt": dict(leftover_paths),
            "endpoints_clean.txt": dict(leftover_endpoints),
        },
    }
    (OUT / "redaction_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print("=== SANITIZATION ===")
    for fname, r in report.items():
        if fname == "re_audit":
            continue
        removed = r["before"] - r["after"]
        print(f"\n{fname}: {r['before']:,} -> {r['after']:,} ({removed:,} removed/dropped)")
        for k, v in r["redacted"].items():
            print(f"  {k:<14} {v:>7,}")

    # ── Gate ────────────────────────────────────────
    failures = []
    for fname, lc in report["re_audit"].items():
        for typ in MUST_BE_ZERO:
            if lc.get(typ, 0) > 0:
                failures.append(f"{fname}: {lc[typ]} surviving {typ}")

    if failures:
        print("\nERROR: sanitization incomplete — sensitive PII survived:")
        for f in failures:
            print(f"  {f}")
        return 1

    print("\nRe-audit passed: no credential/email/phone/id/nip_name survives.")
    print("Sanitized output -> data/sanitized/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
