"""
context.py - Timestamp type detection and hybrid slug classification.
"""

import re

from .constants import (
    DATE_PATH_REGEX,
    FILE_DATE_REGEX,
    ISO_DATE_REGEX,
    ISO_DATETIME_REGEX,
    UNIX_MS_REGEX,
    UNIX_S_REGEX,
)


def detect_type(raw: str) -> str:
    """
    Identify the dominant timestamp type.

    Returns: "unix_ms" | "unix_s" | "iso_datetime" | "date_path" | "iso_date" | "none"
    Priority: unix_ms > unix_s > iso_datetime > date_path > iso_date
    """
    if UNIX_MS_REGEX.search(raw):
        return "unix_ms"
    if UNIX_S_REGEX.search(raw):
        return "unix_s"
    if ISO_DATETIME_REGEX.search(raw):
        return "iso_datetime"
    if DATE_PATH_REGEX.search(raw):
        return "date_path"
    if ISO_DATE_REGEX.search(raw) or FILE_DATE_REGEX.search(raw):
        return "iso_date"
    return "none"


def is_hybrid_slug(raw: str) -> bool:
    """
    Date path + readable words = CMS hybrid slug.

        /2026/06/12/menteri-pendidikan  -> True  (still slug, time-scoped)
        /2026/06/12/                    -> False (archive listing only)
    """
    if not DATE_PATH_REGEX.search(raw):
        return False

    parts = raw.split("/")
    readable_after: list[str] = []
    found_date = False

    for i, p in enumerate(parts):
        if (
            not found_date
            and p.isdigit()
            and len(p) == 4
            and i + 2 < len(parts)
            and parts[i + 1].isdigit()
            and parts[i + 2].isdigit()
        ):
            found_date = True
            continue
        if found_date and p:
            sub_toks = re.split(r"[-_]", p)
            readable_after.extend(
                t
                for t in sub_toks
                if t.isalpha() and len(t) >= 3 and t not in ("http:", "https:")
            )

    return len(readable_after) > 0
