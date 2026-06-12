"""
scorer.py - Continuous UUID scoring (0.0-1.0), preferred over boolean detection.
"""

import re

from .constants import (
    PENALTY_NON_HEX,
    SCORE_DASH_COUNT,
    SCORE_FULL,
    SCORE_PARTIAL,
    UUID_REGEX,
)


def score(raw: str) -> float:
    """
    Analyst scoring: how UUID-like is this path token?

    0.0 = definitely not UUID-like
    0.4-0.6 = UUID-like substring (partial / embedded)
    0.9-1.0 = strict UUID match

    Signals:
        +0.4  long hex-dash substring present
        +0.9  strict full-match UUID (8-4-4-4-12)
        +0.2  exactly 4 dashes (structural, not linguistic)
        -0.5  non-hex alpha chars (g-z, G-Z) -> penalize
    """
    s = raw.strip()

    val = 0.0

    # Partial: any long hex-dash run (32+ chars)
    if re.search(r"[0-9a-fA-F\-]{32,}", s):
        val += SCORE_PARTIAL

    # Full strict UUID: 8-4-4-4-12
    if UUID_REGEX.fullmatch(s):
        val += SCORE_FULL

    # Non-UUID alphabet chars -> penalize
    if re.search(r"[g-zG-Z]", s):
        val += PENALTY_NON_HEX

    # Structural hyphen count
    if s.count("-") == 4:
        val += SCORE_DASH_COUNT

    return min(max(val, 0.0), 1.0)
