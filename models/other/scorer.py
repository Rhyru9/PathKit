"""
scorer.py - Catch-all scoring for internal routing artifacts (not slugs).
"""

import re

from .constants import (
    ASSET_EXT_REGEX,
    DOTTED_VERSION_REGEX,
    FILE_EXT_REGEX,
    ID_CODE_REGEX,
    NUM_DASH_REGEX,
    ORG_UNIT_REGEX,
    RANDOM_ALNUM_REGEX,
    SCORE_ASSET_EXT,
    SCORE_DOTTED_VERSION,
    SCORE_FILE_EXT,
    SCORE_ID_CODE,
    SCORE_NUM_DASH,
    SCORE_NUMERIC_ID,
    SCORE_ORG_UNIT,
    SCORE_RANDOM_ALNUM,
    SCORE_VERSION_1DOT,
    SHORT_NUMERIC_REGEX,
    VERSION_1DOT_REGEX,
)


def _is_random_alnum(raw: str) -> bool:
    """Random token: mixed case + has digits + 5-12 alphanumeric chars."""
    return (
        RANDOM_ALNUM_REGEX.match(raw) is not None
        and re.search(r"\d", raw) is not None
        and re.search(r"[A-Z]", raw) is not None
        and re.search(r"[a-z]", raw) is not None
    )


def score(raw: str) -> float:
    """
    Catch-all: how likely is this a system artifact (not a slug)?

    0.0 = probably a slug or content
    0.5 = short numeric ID
    0.7 = version codes, random alphanumeric
    0.8 = org unit, ID code, static asset, document file

    Applied AFTER uuid/timestamp/hash/base64 detectors.
    """
    val = 0.0

    if ORG_UNIT_REGEX.search(raw):
        val += SCORE_ORG_UNIT

    if ID_CODE_REGEX.match(raw):
        val += SCORE_ID_CODE

    if DOTTED_VERSION_REGEX.search(raw):
        val += SCORE_DOTTED_VERSION

    if VERSION_1DOT_REGEX.match(raw):
        val += SCORE_VERSION_1DOT

    if SHORT_NUMERIC_REGEX.match(raw):
        val += SCORE_NUMERIC_ID

    if _is_random_alnum(raw):
        val += SCORE_RANDOM_ALNUM

    if NUM_DASH_REGEX.match(raw):
        val += SCORE_NUM_DASH

    if ASSET_EXT_REGEX.search(raw):
        val += SCORE_ASSET_EXT

    if FILE_EXT_REGEX.search(raw):
        val += SCORE_FILE_EXT

    return min(val, 1.0)
