"""
models.hash - Structured hash detection for URL path classifier.

Analyst view: Hash is a content-addressed pointer ->
non-semantic system artifact (highest entropy, lowest semantics).

Modules
-------
constants : Hash patterns, scoring weights, context labels.
scorer    : Continuous hash score (0.0-1.0).
context   : Type detection, bundler chunk, embedded detection.

Usage
-----
    from models.hash import score, detect_type, is_bundler_chunk, is_hash_embedded

    score("9e107d9d372bb6826bd81d3542a419d6")       # -> 0.8 (md5)
    score("/chunk/2441aee32022b479.js")             # -> 0.5 (truncated, bundler)
    detect_type("9e107d9d37...")                    # -> "md5"
    is_bundler_chunk("/chunk/2441aee....js")         # -> True
    is_hash_embedded("/article/9e107d9d-panduan")   # -> True
"""

from .context import detect_type, is_bundler_chunk, is_hash_embedded
from .scorer import score

__all__ = [
    "score",
    "detect_type",
    "is_bundler_chunk",
    "is_hash_embedded",
]
