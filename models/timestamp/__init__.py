"""
models.timestamp - Structured timestamp detection for URL path classifier.

Analyst view: Timestamp is a temporal access pattern SIGNAL,
not just a format pattern.

Modules
-------
constants : Timestamp patterns, scoring weights, context labels.
scorer    : Continuous timestamp score (0.0-1.0).
context   : Type detection and hybrid slug classification.

Usage
-----
    from models.timestamp import score, detect_type, is_hybrid_slug

    score("/log/1718201234")                     # -> 0.7
    score("/2026/06/12/menteri-pendidikan")       # -> 0.6
    detect_type("/log/1718201234")               # -> "unix_s"
    is_hybrid_slug("/2026/06/12/menteri")        # -> True
"""

from .context import detect_type, is_hybrid_slug
from .scorer import score

__all__ = [
    "score",
    "detect_type",
    "is_hybrid_slug",
]
