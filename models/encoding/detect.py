"""
detect.py - Detect the primary encoding type of a URL path token.
"""

from .constants import (
    DOUBLE_ENCODE_RE,
    HEX_ENCODE_RE,
    JWT_RE,
    NON_ASCII_RE,
    UNICODE_ESCAPE_RE,
    URL_ENCODE_RE,
    EncodingType,
)


def detect_type(raw: str) -> str:
    """
    Detect the dominant encoding type.

    Priority (most specific first):
        double > base64 > unicode > urlencode > hex > ascii

    Returns an EncodingType value string.
    """
    if DOUBLE_ENCODE_RE.search(raw):
        return EncodingType.DOUBLE.value

    if JWT_RE.search(raw):
        return EncodingType.BASE64.value

    if UNICODE_ESCAPE_RE.search(raw) or NON_ASCII_RE.search(raw):
        return EncodingType.UNICODE.value

    if URL_ENCODE_RE.search(raw):
        return EncodingType.URLENCODE.value

    # Hex =XX only appears AFTER url-decode, so check it after urlencode
    if HEX_ENCODE_RE.search(raw):
        return EncodingType.HEX.value

    return EncodingType.ASCII.value


def has_encoding(raw: str) -> bool:
    """True if the token uses any encoding beyond plain ASCII."""
    return detect_type(raw) != EncodingType.ASCII.value
