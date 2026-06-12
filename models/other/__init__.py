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
    from models.other import score, detect_type

    score("ditjen=5Fbudaya=5Fsesditjen=5Fupt26")  # -> 0.8
    score("PED003.3.4")                            # -> 0.7
    score("70032380")                              # -> 0.5
    score("panduan-belajar-online")                # -> 0.0
"""

from .context import detect_type
from .scorer import score

__all__ = [
    "score",
    "detect_type",
]
