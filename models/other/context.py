"""
context.py - "Other" type detection (org units, dotted versions, numeric IDs).
"""

from .constants import (
    DOTTED_VERSION_REGEX,
    ORG_UNIT_REGEX,
    SHORT_NUMERIC_REGEX,
)


def detect_type(raw: str) -> str:
    """
    Returns: "org_unit" | "dotted_version" | "numeric_id" | "none"
    """
    if ORG_UNIT_REGEX.search(raw):
        return "org_unit"
    if DOTTED_VERSION_REGEX.search(raw):
        return "dotted_version"
    if SHORT_NUMERIC_REGEX.match(raw):
        return "numeric_id"
    return "none"
