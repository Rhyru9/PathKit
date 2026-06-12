"""
hash/detector.py - Hash scoring model for URL path token analysis.

Developer vs Analyst view:

    Developer: Hash = output of crypto function
    Analyst:   Hash = content-addressed pointer
               -> non-semantic system artifact (highest entropy, lowest semantics)

This module implements the **analyst scoring model**:
    - hash_score: continuous 0.0-1.0
    - hash_type: md5, sha1, sha256, truncated, generic, none
    - key rule: hash alone = NOT slug -> API/storage object
"""

import math
import re
from collections import Counter
from enum import Enum


class HashType(Enum):
    NONE = "none"
    MD5 = "md5"  # 32 hex
    SHA1 = "sha1"  # 40 hex
    SHA256 = "sha256"  # 64 hex
    TRUNCATED = "truncated"  # 8-16 hex (bundler chunks)
    GENERIC = "generic"  # other long hex


# ── Patterns ──────────────────────────────────────

MD5_REGEX = re.compile(r"\b[a-f0-9]{32}\b", re.IGNORECASE)
SHA1_REGEX = re.compile(r"\b[a-f0-9]{40}\b", re.IGNORECASE)
SHA256_REGEX = re.compile(r"\b[a-f0-9]{64}\b", re.IGNORECASE)
GENERIC_HEX_REGEX = re.compile(r"\b[a-f0-9]{24,128}\b", re.IGNORECASE)
# Truncated: must contain at least one hex letter (a-f), not just digits
TRUNCATED_HEX_REGEX = re.compile(r"\b(?=[a-f0-9]*[a-f])[a-f0-9]{8,16}\b", re.IGNORECASE)

# UUID pattern - used to skip UUIDs that look like truncated hashes
UUID_LIKE_REGEX = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)

# Bundler chunk: <hash>.js/.css/.map (8-32 hex chars)
BUNDLER_CHUNK_REGEX = re.compile(r"[a-f0-9]{8,32}\.(js|css|map)$", re.IGNORECASE)


# ── Entropy ───────────────────────────────────────


def char_entropy(s: str) -> float:
    """Shannon entropy of character distribution."""
    if not s:
        return 0.0
    freq = Counter(s)
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in freq.values())


def hex_diversity_ratio(s: str) -> float:
    """
    Ratio of unique chars to length. High for hashes (~0.5+),
    low for repeating patterns (~0.1).
    """
    hex_only = re.sub(r"[^a-f0-9]", "", s.lower())
    if not hex_only:
        return 0.0
    return len(set(hex_only)) / len(hex_only)


# ── Scoring Model ─────────────────────────────────


def hash_score(raw: str) -> float:
    """
    Analyst scoring: how hash-like is this path?

    0.0 = no hash signals
    0.4-0.6 = generic long hex
    0.7-1.0 = strong hash (MD5, SHA1, SHA256)

    Signals:
        +0.8  MD5 (32 hex)
        +0.85 SHA1 (40 hex)
        +0.9  SHA256 (64 hex)
        +0.6  generic long hex (24+ chars)
        +0.3  truncated hex (8-16 chars)
        +0.2  high character diversity (entropy > 0.7)
    """
    s = raw.lower()
    val = 0.0

    # If this is a UUID, the UUID detector should handle it - don't double-count as hash
    if UUID_LIKE_REGEX.search(s):
        return 0.0

    if SHA256_REGEX.search(s):
        val += 0.9
    elif SHA1_REGEX.search(s):
        val += 0.85
    elif MD5_REGEX.search(s):
        val += 0.8
    elif GENERIC_HEX_REGEX.search(s):
        val += 0.6
    elif TRUNCATED_HEX_REGEX.search(s):
        val += 0.3

    # Entropy bonus: hashes have highly diverse character distribution
    if val > 0.0:
        diversity = hex_diversity_ratio(s)
        if diversity > 0.5:
            val += 0.2

    return min(val, 1.0)


# ── Type Detection ────────────────────────────────


def detect_type(raw: str) -> str:
    """
    Identify the dominant hash type.

    Returns: "sha256" | "sha1" | "md5" | "truncated" | "generic" | "none"
    Priority: sha256 > sha1 > md5 > truncated > generic
    """
    # UUIDs belong to the UUID detector, not hash
    if UUID_LIKE_REGEX.search(raw):
        return "none"
    if SHA256_REGEX.search(raw):
        return "sha256"
    if SHA1_REGEX.search(raw):
        return "sha1"
    if MD5_REGEX.search(raw):
        return "md5"
    if TRUNCATED_HEX_REGEX.search(raw):
        return "truncated"
    if GENERIC_HEX_REGEX.search(raw):
        return "generic"
    return "none"


# ── Context Detection ─────────────────────────────


def is_bundler_chunk(raw: str) -> bool:
    """
    Hashes in bundler artifacts: name-<hash>.js
    /chunk/main-9e107d9d372bb6bd.js
    """
    return bool(BUNDLER_CHUNK_REGEX.search(raw))


def is_hash_embedded(raw: str) -> bool:
    """
    Hash mixed with readable tokens via hyphens/underscores in the SAME segment.
    /article/9e107d9d-panduan -> True  (CMS hybrid leak)
    /file/a94a8fe...          -> False (path prefix, hash is isolated)
    """
    if detect_type(raw) == "none":
        return False
    # Split on path separators - check each segment individually
    segments = re.split(r"[/]", raw.lower())
    for seg in segments:
        # If this segment contains a hash AND has readable tokens
        if GENERIC_HEX_REGEX.search(seg) or TRUNCATED_HEX_REGEX.search(seg):
            toks = re.split(r"[-_]", seg)
            readable = [t for t in toks if t.isalpha() and len(t) >= 3]
            if readable:
                return True
    return False


# ── Decision Logic ────────────────────────────────


def classify_hint(raw: str) -> str | None:
    """
    Heuristic classification based on hash signals.

    Returns: "asset" | "file" | "api" | "review" | None
    """
    score = hash_score(raw)
    if score < 0.5:
        return None

    # Bundler chunk -> asset
    if is_bundler_chunk(raw):
        return "asset"

    # Hash + readable text -> CMS hybrid (review)
    if is_hash_embedded(raw):
        return "review"

    # Hash alone -> API / storage object
    return "api"


# ── Full Analysis ─────────────────────────────────


def analyze(raw: str) -> dict:
    """
    Full hash analysis for a path token.
    """
    return {
        "hash_score": hash_score(raw),
        "hash_type": detect_type(raw),
        "is_bundler_chunk": is_bundler_chunk(raw),
        "is_hash_embedded": is_hash_embedded(raw),
        "hex_diversity": round(hex_diversity_ratio(raw), 3),
        "classification_hint": classify_hint(raw),
    }


# ── Unified Identifier Scores ─────────────────────


def identifier_type_scores(raw: str) -> dict[str, float]:
    """
    Compare all identifier types at once.
    Each score is 0.0-1.0 independently.

    This is the key integration point:
        high hash_score -> push away from slug, toward asset/api.
    """
    return {
        "uuid": _try_uuid_score(raw),
        "timestamp": _try_timestamp_score(raw),
        "hash": hash_score(raw),
    }


def _try_uuid_score(raw: str) -> float:
    try:
        from researchs.uuid.detector import uuid_score

        return uuid_score(raw)
    except ImportError:
        return 0.0


def _try_timestamp_score(raw: str) -> float:
    try:
        from researchs.timestamps.detector import timestamp_score

        return timestamp_score(raw)
    except ImportError:
        return 0.0


# ── Demo ──────────────────────────────────────────

if __name__ == "__main__":
    samples = [
        "9e107d9d372bb6826bd81d3542a419d6",  # md5
        "/chunk/2441aee32022b479.js",  # bundled chunk
        "/file/a94a8fe5ccb19ba61c4c0873d391e987982fbbd3",  # sha1
        "/article/9e107d9d372bb6bd-panduan-belajar",  # hash embedded
        "panduan-belajar-online",  # no hash
        "a1b2",  # too short
        "3a7bd3e2360a3d1c7c0e3f2b2f6a9c1d",  # sha256-like
    ]

    print(
        f"{'PATH':<55} {'SCORE':>6} {'TYPE':>10} {'BUNDLE':>7} {'EMBED':>7} {'-> HINT'}"
    )
    print("-" * 105)
    for raw in samples:
        a = analyze(raw)
        ids = identifier_type_scores(raw)
        print(
            f"{raw[:53]:<55} {a['hash_score']:>6.2f} "
            f"{a['hash_type']:>10} "
            f"{str(a['is_bundler_chunk']):>7} "
            f"{str(a['is_hash_embedded']):>7} "
            f" -> {a['classification_hint'] or '-'}"
        )

    print("\n  identifier_type_scores for md5:")
    print(f"    {identifier_type_scores(samples[0])}")
