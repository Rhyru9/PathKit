"""
features.py - UUID-specific features for classifier feature vectors.
"""

import math
import re
from collections import Counter

from .constants import UUID_REGEX


def hex_entropy(s: str) -> float:
    """Shannon entropy - high for uniform hex, low for natural language."""
    if not s:
        return 0.0
    freq = Counter(s)
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in freq.values())


def is_hex_uniform(s: str) -> bool:
    """
    All chars are in [0-9a-f] with length >= 32 -> UUID-like distribution.
    """
    hex_only = re.sub(r"[-]", "", s)
    return bool(re.fullmatch(r"[0-9a-fA-F]+", hex_only)) and len(hex_only) >= 32


def is_semantically_isolated(s: str) -> bool:
    """
    UUID tokens are never real words.
    Returns True if no readable words (3+ alpha chars) exist in the string.
    """
    toks = re.split(r"[-_/.\s]+", s)
    readable = [t for t in toks if t.isalpha() and len(t) >= 3]
    return len(readable) == 0


def has_embedded_uuid(s: str) -> bool:
    """
    UUID exists inside a larger string that also contains readable text.
    This is a CMS hybrid pattern - a negative signal for slug classification.
    """
    if not UUID_REGEX.search(s):
        return False
    return not UUID_REGEX.fullmatch(s) and not is_semantically_isolated(s)
