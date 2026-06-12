"""
scorer.py - Continuous hash scoring (0.0-1.0).
"""

from .constants import (
    DIVERSITY_THRESHOLD,
    GENERIC_HEX_REGEX,
    MD5_REGEX,
    SCORE_DIVERSITY_BONUS,
    SCORE_GENERIC,
    SCORE_MD5,
    SCORE_SHA1,
    SCORE_SHA256,
    SCORE_TRUNCATED,
    SHA1_REGEX,
    SHA256_REGEX,
    TRUNCATED_HEX_REGEX,
    UUID_LIKE_REGEX,
)


def hex_diversity_ratio(s: str) -> float:
    """Ratio of unique hex chars to length. High for hashes (~0.5+)."""
    hex_only = ""
    for c in s.lower():
        if c in "abcdef0123456789":
            hex_only += c
    if not hex_only:
        return 0.0
    return len(set(hex_only)) / len(hex_only)


def score(raw: str) -> float:
    """
    Analyst scoring: how hash-like is this path?

    0.0 = no hash signals (or UUID - those belong to models.uuid)
    0.3 = truncated hex (8-16 chars)
    0.6-0.8 = generic/MD5
    0.85-1.0 = SHA1/SHA256

    Signals:
        +0.9  SHA256 (64 hex)
        +0.85 SHA1 (40 hex)
        +0.8  MD5 (32 hex)
        +0.6  generic long hex (24+ chars)
        +0.3  truncated hex (8-16 chars, must have [a-f])
        +0.2  high hex diversity bonus (>0.5 unique ratio)
    """
    s = raw.lower()

    # UUIDs belong to models.uuid - don't double-count
    if UUID_LIKE_REGEX.search(s):
        return 0.0

    val = 0.0

    if SHA256_REGEX.search(s):
        val += SCORE_SHA256
    elif SHA1_REGEX.search(s):
        val += SCORE_SHA1
    elif MD5_REGEX.search(s):
        val += SCORE_MD5
    elif GENERIC_HEX_REGEX.search(s):
        val += SCORE_GENERIC
    elif TRUNCATED_HEX_REGEX.search(s):
        val += SCORE_TRUNCATED

    if val > 0.0 and hex_diversity_ratio(s) > DIVERSITY_THRESHOLD:
        val += SCORE_DIVERSITY_BONUS

    return min(val, 1.0)
