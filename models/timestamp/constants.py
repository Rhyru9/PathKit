"""
constants.py - Timestamp patterns, scoring weights, and context labels.
"""

import re

# ── Patterns ──────────────────────────────────────

# Unix seconds: realistic range 1,600,000,000 (2020) - 2,999,999,999 (2065)
UNIX_S_REGEX = re.compile(r"\b(1[6-9]\d{8}|2\d{9})\b")

# Unix milliseconds: 13-digit number starting with 1
UNIX_MS_REGEX = re.compile(r"\b1\d{12}\b")

# ISO date: YYYY-MM-DD
ISO_DATE_REGEX = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")

# ISO datetime: YYYY-MM-DD[Tt]HH:MM:SS
ISO_DATETIME_REGEX = re.compile(r"\b\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}")

# Date path: /YYYY/MM/DD/
DATE_PATH_REGEX = re.compile(r"/\d{4}/\d{2}/\d{2}/")

# File-style date: YYYY-MM-DD_HH-MM-SS
FILE_DATE_REGEX = re.compile(r"\d{4}[-_]\d{2}[-_]\d{2}")

# ── Scoring weights ───────────────────────────────

SCORE_UNIX_S = 0.7
SCORE_UNIX_MS = 0.8
SCORE_ISO_DATE = 0.5
SCORE_ISO_DATETIME = 0.7
SCORE_DATE_PATH = 0.6
SCORE_FILE_DATE = 0.3

# ── Context labels ────────────────────────────────

CONTEXT_CLASSES = {
    "unix_s": "api",  # log/system endpoint -> API
    "unix_ms": "api",  # real-time analytics -> API
    "iso_datetime": "api",  # audit/snapshot -> API
    "date_path": "search",  # archive listing -> search
    "iso_date": "file",  # timestamped file -> file
}
