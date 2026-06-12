"""
constants.py - "Other" patterns, scoring weights, and context labels.

"Other" = catch-all for internal routing artifacts that are not slugs
and not identifiers (UUID/timestamp/hash/base64).
"""

import re

# ── Patterns ──────────────────────────────────────

# Org unit chain: ditjen=5Fbudaya=5Fsesditjen=5Fupt26
ORG_UNIT_REGEX = re.compile(r"(?:[a-z]+=5F){2,}[a-z0-9]+", re.IGNORECASE)

# Dotted version: PED003.3.4, KR03.005.03
DOTTED_VERSION_REGEX = re.compile(
    r"\b[A-Z]{2,5}\d{2,4}\.\d{1,3}\.\d{1,3}", re.IGNORECASE
)

# Short pure numeric ID: 5-10 digits (not a timestamp range)
SHORT_NUMERIC_REGEX = re.compile(r"^\d{5,10}$")

# ── Scoring weights ───────────────────────────────

SCORE_ORG_UNIT = 0.8
SCORE_DOTTED_VERSION = 0.7
SCORE_NUMERIC_ID = 0.5

# ── Context labels ────────────────────────────────

CONTEXT_CLASSES = {
    "org_unit": "file",  # internal routing code
    "dotted_version": "file",  # versioned document reference
    "numeric_id": "file",  # employee/doc ID
}
