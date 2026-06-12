"""
scorer.py - Catch-all scoring for internal routing artifacts (not slugs).
"""

from .constants import (
    DOTTED_VERSION_REGEX,
    ORG_UNIT_REGEX,
    SCORE_DOTTED_VERSION,
    SCORE_NUMERIC_ID,
    SCORE_ORG_UNIT,
    SHORT_NUMERIC_REGEX,
)


def score(raw: str) -> float:
    """
    Catch-all: how likely is this a system artifact (not a slug)?

    0.0 = probably a slug or content
    0.5 = short numeric ID
    0.7 = dotted version path
    0.8 = org unit routing code

    Applied AFTER uuid/timestamp/hash/base64 detectors.
    """
    val = 0.0

    if ORG_UNIT_REGEX.search(raw):
        val += SCORE_ORG_UNIT

    if DOTTED_VERSION_REGEX.search(raw):
        val += SCORE_DOTTED_VERSION

    if SHORT_NUMERIC_REGEX.match(raw):
        val += SCORE_NUMERIC_ID

    return min(val, 1.0)
