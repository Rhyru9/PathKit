"""
models.uuid - Structured UUID detection and scoring for URL path classifier.

Analyst view: UUID is a high-confidence non-semantic identifier SIGNAL,
not just a format pattern.

Modules
-------
constants : UUID patterns, scoring weights, context labels.
scorer    : Continuous uuid score (0.0-1.0).
context   : Context detection (standalone, embedded, asset, query).
features  : Hex uniformity, semantic isolation, entropy.

Usage
-----
    from models.uuid import score, detect, has_embedded_uuid

    score("550e8400-e29b-41d4-a716-446655440000")       # -> 1.0
    score("/article/panduan-belajar-online")             # -> 0.0
    detect("550e8400-e29b-41d4-a716-446655440000")       # -> "standalone"
    detect("/article/550e8400...panduan")                # -> "embedded"
    has_embedded_uuid("/article/550e8400...panduan")      # -> True
"""

from .context import detect
from .features import (
    has_embedded_uuid,
    hex_entropy,
    is_hex_uniform,
    is_semantically_isolated,
)
from .scorer import score

__all__ = [
    "score",
    "detect",
    "has_embedded_uuid",
    "hex_entropy",
    "is_hex_uniform",
    "is_semantically_isolated",
]
