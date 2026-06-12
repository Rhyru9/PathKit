"""
scorer.py - Continuous base64 scoring (0.0-1.0).
"""

from .constants import (
    CLASSIC_B64_REGEX,
    DIVERSITY_THRESHOLD,
    JWT_REGEX,
    SCORE_CLASSIC,
    SCORE_DIVERSITY_BONUS,
    SCORE_JWT,
)


def _has_mixed_case(s: str) -> bool:
    """Real Base64 has both upper and lowercase."""
    import re

    return bool(re.search(r"[A-Z]", s)) and bool(re.search(r"[a-z]", s))


def _has_base64_signal(s: str) -> bool:
    """Real Base64 has + or / - pure alphanumeric is not Base64."""
    import re

    return bool(re.search(r"[+/]", s)) and _has_mixed_case(s)


def _alphabet_size(s: str) -> int:
    """Count unique chars in base64 alphabet (A-Za-z0-9+/=)."""
    return len({c for c in s if c.isalnum() or c in "+/=-_"})


def score(raw: str) -> float:
    """
    Analyst scoring: how Base64-like is this path?

    0.0 = no signals
    0.7+ = classic Base64 (mixed case + +/=)
    0.9+ = JWT/Laravel encrypted token (eyJ prefix)

    Base64 = encrypted/encoded data -> NEVER a slug.
    """
    val = 0.0

    if JWT_REGEX.search(raw):
        val += SCORE_JWT

    m = CLASSIC_B64_REGEX.search(raw)
    if m and _has_base64_signal(m.group()):
        val += SCORE_CLASSIC

    if val > 0.0 and _alphabet_size(raw) > DIVERSITY_THRESHOLD:
        val += SCORE_DIVERSITY_BONUS

    return min(val, 1.0)
