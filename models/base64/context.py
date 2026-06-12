"""
context.py - Base64 type detection.
"""

from .constants import CLASSIC_B64_REGEX, JWT_REGEX
from .scorer import _has_base64_signal


def detect_type(raw: str) -> str:
    """
    Returns: "jwt" | "classic" | "none"
    """
    if JWT_REGEX.search(raw):
        return "jwt"

    m = CLASSIC_B64_REGEX.search(raw)
    if m and _has_base64_signal(m.group()):
        return "classic"

    return "none"


def is_in_query(raw: str) -> bool:
    """Base64 token appears in a query string."""
    return "?" in raw and "=" in raw
