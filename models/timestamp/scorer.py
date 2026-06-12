"""
scorer.py - Continuous timestamp scoring (0.0-1.0).
"""

from .constants import (
    DATE_PATH_REGEX,
    FILE_DATE_REGEX,
    ISO_DATE_REGEX,
    ISO_DATETIME_REGEX,
    SCORE_DATE_PATH,
    SCORE_FILE_DATE,
    SCORE_ISO_DATE,
    SCORE_ISO_DATETIME,
    SCORE_UNIX_MS,
    SCORE_UNIX_S,
    UNIX_MS_REGEX,
    UNIX_S_REGEX,
)


def score(raw: str) -> float:
    """
    Analyst scoring: how timestamp-heavy is this path?

    0.0 = no timestamp signals
    0.4-0.6 = weak date-like pattern
    0.7-1.0 = strong timestamp (likely system/API endpoint)

    Signals:
        +0.7  unix seconds (realistic range: 1.6B-3.0B)
        +0.8  unix milliseconds
        +0.5  ISO date YYYY-MM-DD
        +0.7  ISO datetime YYYY-MM-DDTHH:MM:SS
        +0.6  date path /YYYY/MM/DD/
        +0.3  file-style date YYYY-MM-DD_HH-MM-SS
    """
    val = 0.0

    # Unix timestamps (mutually exclusive: ms before s)
    if UNIX_MS_REGEX.search(raw):
        val += SCORE_UNIX_MS
    elif UNIX_S_REGEX.search(raw):
        val += SCORE_UNIX_S

    if DATE_PATH_REGEX.search(raw):
        val += SCORE_DATE_PATH

    # ISO variants (mutually exclusive: datetime before date)
    if ISO_DATETIME_REGEX.search(raw):
        val += SCORE_ISO_DATETIME
    elif ISO_DATE_REGEX.search(raw):
        val += SCORE_ISO_DATE

    if FILE_DATE_REGEX.search(raw):
        val += SCORE_FILE_DATE

    return min(val, 1.0)
