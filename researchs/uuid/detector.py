"""
uuid/detector.py - UUID scoring model for URL path token analysis.

Developer vs Analyst view:

    Developer: UUID = format string (8-4-4-4-12)
    Analyst:   UUID = high-confidence non-semantic identifier SIGNAL

This module implements the **analyst scoring model**:
    - uuid_score: continuous 0.0-1.0 (not just True/False)
    - uuid context: standalone, embedded, mixed, asset-style
"""

import math
import re
from collections import Counter
from enum import Enum

# ── UUID Pattern (RFC 4122) ─────────────────────────

UUID_REGEX = re.compile(
    r"[0-9a-fA-F]{8}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{12}"
)

# Extended: also catch stripped/non-standard UUID-like hex-dash strings
UUID_LOOSE_REGEX = re.compile(r"[0-9a-fA-F]{8,}-[0-9a-fA-F]{4,}-[0-9a-fA-F]{4,}")


class UUIDContext(Enum):
    NONE = "none"  # no UUID detected
    STANDALONE = "standalone"  # UUID is the entire string
    EMBEDDED = "embedded"  # UUID inside larger string (CMS hybrid)
    ASSET = "asset"  # UUID + file extension
    QUERY = "query"  # UUID in query param


# ── Scoring Model ──────────────────────────────────


def uuid_score(s: str) -> float:
    """
    Analyst scoring: how UUID-like is this string?
    Continuous 0.0-1.0 (preferred over boolean is_uuid).

    Signals:
        +0.4  long hex-dash substring present
        +0.9  strict full-match UUID
        +0.2  exactly 4 dashes (structural)
        -0.5  non-hex alpha chars (g-z, G-Z) -> penalize
    """
    score = 0.0

    # Partial: any long hex-dash run
    if re.search(r"[0-9a-fA-F\-]{32,}", s):
        score += 0.4

    # Full strict UUID: 8-4-4-4-12
    if re.fullmatch(
        r"[0-9a-fA-F]{8}-"
        r"[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{12}",
        s,
    ):
        score += 0.9

    # Non-UUID alphabet chars -> penalize
    if re.search(r"[g-zG-Z]", s):
        score -= 0.5

    # Structural hyphen count
    if s.count("-") == 4:
        score += 0.2

    return min(max(score, 0.0), 1.0)


# ── Context Detection ──────────────────────────────


def detect_context(raw: str) -> UUIDContext:
    """
    Classify UUID context - determines what the path IS, not just format.
    """
    s = raw.strip().lower()

    if not UUID_REGEX.search(s):
        return UUIDContext.NONE

    # Asset: UUID + file extension
    if re.search(r"\.(js|css|png|jpg|jpeg|gif|svg|webp|pdf|json|xml)$", s):
        return UUIDContext.ASSET

    # Query: UUID in query params
    if "?" in s and "=" in s:
        return UUIDContext.QUERY

    # Standalone: entire string is UUID
    if UUID_REGEX.fullmatch(s):
        return UUIDContext.STANDALONE

    # Embedded: UUID inside larger text (CMS hybrid)
    return UUIDContext.EMBEDDED


# ── Entropy Analysis ───────────────────────────────


def hex_entropy(s: str) -> float:
    """Shannon entropy of a string (specialized for hex detection)."""
    if not s:
        return 0.0
    freq = Counter(s)
    L = len(s)
    return -sum((c / L) * math.log2(c / L) for c in freq.values())


def is_hex_uniform(s: str) -> bool:
    """
    Check if character distribution looks UUID-like (uniform hex).
    True = all chars are in [0-9a-f] with high entropy.
    """
    hex_only = re.sub(r"[-]", "", s)
    return bool(re.fullmatch(r"[0-9a-fA-F]+", hex_only)) and len(hex_only) >= 32


# ── Semantic Isolation ─────────────────────────────


def is_semantically_isolated(uuid_part: str) -> bool:
    """
    UUID tokens are never real words - check that there are no
    readable words mixed in with the UUID portion.
    """
    toks = re.split(r"[-_/.\s]+", uuid_part)
    readable = [t for t in toks if t.isalpha() and len(t) >= 3 and not t.isnumeric()]
    return len(readable) == 0


# ── Convenience: full analysis ─────────────────────


def analyze(raw: str) -> dict:
    """
    Full UUID analysis for a path token.
    Returns score, context, entropy, and semantic signals.
    """
    s = raw.strip().lower()
    context = detect_context(raw)
    return {
        "uuid_score": uuid_score(s),
        "uuid_context": context.value,
        "is_hex_uniform": is_hex_uniform(s),
        "is_semantically_isolated": is_semantically_isolated(s),
        "has_uuid": context != UUIDContext.NONE,
        "is_standalone_uuid": context == UUIDContext.STANDALONE,
        "is_embedded_uuid": context == UUIDContext.EMBEDDED,
    }


# -- Mapping: context -> classification -------------

CONTEXT_TO_CLASS = {
    UUIDContext.STANDALONE: "random_id",  # UUID alone -> API/object
    UUIDContext.EMBEDDED: "review",  # CMS hybrid -> review
    UUIDContext.ASSET: "asset",  # UUID + ext -> CDN asset
    UUIDContext.QUERY: "search",  # UUID + ?= -> search/API
}

# ── Demo ──────────────────────────────────────────

if __name__ == "__main__":
    samples = [
        "550e8400-e29b-41d4-a716-446655440000",  # standalone uuid
        "/article/550e8400-e29b-41d4-a716-446655440000",  # embedded in path
        "panduan-belajar-online",  # normal slug
        "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",  # hex hash (not uuid)
        "/img/550e8400-e29b-41d4-a716-446655440000.png",  # uuid asset
        "%2Farticle%2F550e8400-e29b-41d4-a716",  # url-encoded uuid
    ]

    print(f"{'PATH':<55} {'SCORE':>6} {'CTX':>12} {'UNIF':>6} {'ISOL':>6} {'-> CLASS'}")
    print("-" * 105)
    for raw in samples:
        a = analyze(raw)
        cls = CONTEXT_TO_CLASS.get(UUIDContext(a["uuid_context"]), "?")
        print(
            f"{raw[:52]:<55} {a['uuid_score']:>6.2f} "
            f"{a['uuid_context']:>12} "
            f"{str(a['is_hex_uniform']):>6} "
            f"{str(a['is_semantically_isolated']):>6} "
            f" -> {cls}"
        )
