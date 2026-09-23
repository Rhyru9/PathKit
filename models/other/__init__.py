"""
models.other - Catch-all non-slug detector for internal routing artifacts.

These are NOT identifiers (uuid/timestamp/hash/base64) and NOT slugs.
They are internal routing codes, versioned references, org unit IDs.

Applied LAST in the classification pipeline after all identifier detectors.

Modules
-------
constants : Patterns, scoring weights, context labels.
scorer    : Catch-all score (0.0-1.0).
context   : Type detection.

Usage
-----
    from models.other import score, detect_type, classify

    score("ditjen=5Fbudaya=5Fsesditjen=5Fupt26")  # -> 0.8
    score("P9996589")                             # -> 0.8 (id code)
    score("PED001.3")                             # -> 0.7 (single-dot)
    score("vDnPZwVN0j")                           # -> 0.7 (random alnum)
    score("panduan-belajar-online")               # -> 0.0
    classify("P9996589")                          # -> "random_id"
"""

from .context import classify, detect_type
from .scorer import score

__all__ = [
    "score",
    "detect_type",
    "classify",
]
