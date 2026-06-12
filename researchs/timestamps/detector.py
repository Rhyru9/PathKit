"""
timestamps/detector.py - Timestamp scoring model for URL path token analysis.

Developer vs Analyst view:

    Developer: Timestamp = time identifier format
    Analyst:   Timestamp = temporal access pattern SIGNAL
               -> dynamic, time-scoped, non-canonical content

This module implements the **analyst scoring model**:
    - timestamp_score: continuous 0.0-1.0
    - timestamp_type: unix_s, unix_ms, iso_date, date_path, iso_datetime
    - key rule: timestamp + words = CMS hybrid (still slug, but time-scoped)
"""

import re
from enum import Enum


class TimestampType(Enum):
    NONE = "none"
    UNIX_S = "unix_s"  # 1718201234
    UNIX_MS = "unix_ms"  # 1718201234123
    ISO_DATE = "iso_date"  # 2026-06-12
    ISO_DATETIME = "iso_datetime"  # 2026-06-12T10:20:30Z
    DATE_PATH = "date_path"  # /2026/06/12/


# ── Patterns ──────────────────────────────────────

# Unix seconds: realistic range 1,600,000,000 (2020) - 2,999,999,999 (2065)
UNIX_S_REGEX = re.compile(r"\b(1[6-9]\d{8}|2\d{9})\b")

# Unix milliseconds: 13-digit number starting with 1
UNIX_MS_REGEX = re.compile(r"\b1\d{12}\b")

# ISO date: YYYY-MM-DD
ISO_DATE_REGEX = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")

# ISO datetime: YYYY-MM-DD followed by T/t and time, optional Z/timezone
ISO_DATETIME_REGEX = re.compile(r"\b\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}")

# Date path: /YYYY/MM/DD/
DATE_PATH_REGEX = re.compile(r"/\d{4}/\d{2}/\d{2}/")

# URL-encoded date-like: 2026-06-12_10-20-30
FILE_DATE_REGEX = re.compile(r"\d{4}[-_]\d{2}[-_]\d{2}")


# ── Scoring Model ─────────────────────────────────


def timestamp_score(s: str) -> float:
    """
    Analyst scoring: how timestamp-heavy is this path?

    0.0 = no timestamp signals
    0.4-0.6 = weak date-like pattern
    0.7-1.0 = strong timestamp (likely system/API endpoint)

    Signals:
        +0.7  unix seconds (realistic range)
        +0.8  unix milliseconds
        +0.5  ISO date YYYY-MM-DD
        +0.6  date path /YYYY/MM/DD/
        +0.3  file-style date YYYY-MM-DD_HH-MM-SS
    """
    val = 0.0

    if UNIX_MS_REGEX.search(s):
        val += 0.8
    elif UNIX_S_REGEX.search(s):
        val += 0.7

    if DATE_PATH_REGEX.search(s):
        val += 0.6

    if ISO_DATETIME_REGEX.search(s):
        val += 0.7
    elif ISO_DATE_REGEX.search(s):
        val += 0.5

    if FILE_DATE_REGEX.search(s):
        val += 0.3

    return min(val, 1.0)


# ── Type Detection ────────────────────────────────


def detect_type(s: str) -> TimestampType:
    """
    Identify the dominant timestamp type.
    Priority: unix_ms > unix_s > iso_datetime > date_path > iso_date > none
    """
    if UNIX_MS_REGEX.search(s):
        return TimestampType.UNIX_MS
    if UNIX_S_REGEX.search(s):
        return TimestampType.UNIX_S
    if ISO_DATETIME_REGEX.search(s):
        return TimestampType.ISO_DATETIME
    if DATE_PATH_REGEX.search(s):
        return TimestampType.DATE_PATH
    if ISO_DATE_REGEX.search(s) or FILE_DATE_REGEX.search(s):
        return TimestampType.ISO_DATE
    return TimestampType.NONE


# ── Hybrid Detection ──────────────────────────────


def is_hybrid_slug(s: str) -> bool:
    """
    Date path + readable words = CMS hybrid slug.

    Example:
        /2026/06/12/menteri-pendidikan  -> True  (still slug, but time-scoped)
        /2026/06/12/                    -> False (archive listing only)
    """
    if not DATE_PATH_REGEX.search(s):
        return False

    # Check if there are readable tokens AFTER the date path
    parts = s.split("/")
    # After the date-path group (YYYY, MM, DD), check remaining parts
    readable_after = []
    found_date = False
    for i, p in enumerate(parts):
        if not found_date and p.isdigit() and len(p) == 4 and i + 2 < len(parts):
            if parts[i + 1].isdigit() and parts[i + 2].isdigit():
                found_date = True
                continue
        if found_date and p:
            # Split hyphenated tokens to check readability
            sub_toks = re.split(r"[-_]", p)
            readable_after.extend(
                t
                for t in sub_toks
                if t.isalpha() and len(t) >= 3 and t not in ("http:", "https:")
            )
    return len(readable_after) > 0


# ── Decision Logic ────────────────────────────────


def classify_hint(s: str) -> str | None:
    """
    Heuristic classification hint based on timestamp signals.

    Returns:
        "api"      - high-confidence system/API endpoint
        "slug"     - CMS hybrid (date path + readable text, still slug)
        "search"   - timestamp + query
        "file"     - timestamp in filename
        None       - no strong signal
    """
    score = timestamp_score(s)
    ts_type = detect_type(s)

    if score < 0.5:
        return None

    # Strong unix timestamp -> API/system
    if ts_type in (
        TimestampType.UNIX_S,
        TimestampType.UNIX_MS,
        TimestampType.ISO_DATETIME,
    ):
        return "api"

    # Date path + words -> hybrid slug
    if ts_type == TimestampType.DATE_PATH and is_hybrid_slug(s):
        return "slug"

    # Date path alone -> archive/search
    if ts_type == TimestampType.DATE_PATH:
        return "search"

    # ISO date in filename -> file
    if ts_type == TimestampType.ISO_DATE:
        if "?" in s:
            return "search"
        return "file"

    return None


# ── Full Analysis ─────────────────────────────────


def analyze(raw: str) -> dict:
    """
    Full timestamp analysis for a path token.
    """
    s = raw.strip().lower()
    score = timestamp_score(s)
    ts_type = detect_type(s)
    return {
        "timestamp_score": score,
        "timestamp_type": ts_type.value,
        "is_hybrid_slug": is_hybrid_slug(s),
        "has_timestamp": score > 0.0,
        "classification_hint": classify_hint(s),
    }


# ── Demo ──────────────────────────────────────────

if __name__ == "__main__":
    samples = [
        "/log/1718201234",  # unix seconds
        "/event/1718201234123",  # unix ms
        "/2026/06/12/menteri-pendidikan",  # date path + slug
        "/2026/06/12/",  # date path only
        "2026-06-12T10:20:30Z",  # iso datetime
        "2026-06-12",  # iso date
        "panduan-belajar-online",  # no timestamp
        "%282026-06-12%29",  # encoded date
        "backup_2026-06-12_10-20-30.sql",  # file date
    ]

    print(f"{'PATH':<50} {'SCORE':>6} {'TYPE':>14} {'HYBRID':>7} {'-> HINT'}")
    print("-" * 95)
    for raw in samples:
        a = analyze(raw)
        print(
            f"{raw[:48]:<50} {a['timestamp_score']:>6.2f} "
            f"{a['timestamp_type']:>14} "
            f"{str(a['is_hybrid_slug']):>7} "
            f" -> {a['classification_hint'] or '-'}"
        )
