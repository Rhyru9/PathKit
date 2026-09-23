"""
context.py - "Other" type detection and final class mapping.
"""

import re

from .constants import (
    ASSET_EXT_REGEX,
    CONTEXT_CLASSES,
    DOTTED_VERSION_REGEX,
    FILE_EXT_REGEX,
    ID_CODE_REGEX,
    NUM_DASH_REGEX,
    ORG_UNIT_REGEX,
    RANDOM_ALNUM_REGEX,
    SHORT_NUMERIC_REGEX,
    VERSION_1DOT_REGEX,
)


def _is_random_alnum(raw: str) -> bool:
    return (
        RANDOM_ALNUM_REGEX.match(raw) is not None
        and re.search(r"\d", raw) is not None
        and re.search(r"[A-Z]", raw) is not None
        and re.search(r"[a-z]", raw) is not None
    )


def detect_type(raw: str) -> str:
    """
    Returns one of: "org_unit" | "dotted_version" | "version_1dot"
                    "numeric_id" | "id_code" | "random_alnum"
                    "static_asset" | "file_ext" | "none"
    """
    if ORG_UNIT_REGEX.search(raw):
        return "org_unit"
    if ID_CODE_REGEX.match(raw):
        return "id_code"
    if DOTTED_VERSION_REGEX.search(raw):
        return "dotted_version"
    if VERSION_1DOT_REGEX.match(raw):
        return "version_1dot"
    if SHORT_NUMERIC_REGEX.match(raw):
        return "numeric_id"
    if _is_random_alnum(raw):
        return "random_alnum"
    if NUM_DASH_REGEX.match(raw):
        return "num_dash"
    if ASSET_EXT_REGEX.search(raw):
        return "static_asset"
    if FILE_EXT_REGEX.search(raw):
        return "file_ext"
    return "none"


def classify(raw: str) -> str | None:
    """
    Return the final class for a detected "other" artifact, or None if
    this path is not a system artifact.
    """
    t = detect_type(raw)
    if t == "none":
        return None
    return CONTEXT_CLASSES.get(t, "random_id")
