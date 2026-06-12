"""
models.base64 - Structured Base64 detection for URL path classifier.

Analyst view: Base64 = encrypted/encoded data transport ->
strong API/auth signal -> NEVER a slug.

Hash vs Base64:
    Hash    = pure hex [a-f0-9], fixed length, content-addressed (CDN/storage)
    Base64  = full alphabet [A-Za-z0-9+/=], variable length, data transport (auth/session)

Modules
-------
constants : Patterns, scoring weights, context labels.
scorer    : Continuous base64 score (0.0-1.0).
context   : Type detection (jwt, classic).

Usage
-----
    from models.base64 import score, detect_type

    score("eyJpdiI6Ii9CVlVOWkcyeWFxVWY...")   # -> 1.0 (jwt)
    score("panduan-belajar-online")          # -> 0.0
    detect_type("eyJpdiI6...")              # -> "jwt"
"""

from .context import detect_type, is_in_query
from .scorer import score

__all__ = [
    "score",
    "detect_type",
    "is_in_query",
]
