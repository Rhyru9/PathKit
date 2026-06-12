"""
base64/detector.py - Base64 scoring model for URL path token analysis.

Hash vs Base64:

    Hash    = pure hex [a-f0-9], fixed length, content-addressed (CDN/storage)
    Base64  = full alphabet [A-Za-z0-9+/=], variable length, data transport (auth/session)

Analyst view: Base64 = encrypted/encoded data -> NEVER a slug.
"""

import re
from enum import Enum


class Base64Type(Enum):
    NONE = "none"
    JWT = "jwt"  # eyJ... prefix (Laravel/JWT encrypted)
    CLASSIC = "classic"  # [A-Za-z0-9+/=]{40,} with mixed case
    URLSAFE = "urlsafe"  # [A-Za-z0-9\-_]{40,} no padding


# ── Patterns ──────────────────────────────────────

# JWT/Laravel: eyJ = Base64 of '{"'
JWT_REGEX = re.compile(r"eyJ[A-Za-z0-9+/=]{40,}")

# Classic Base64: must contain + or / (standard alphabet, not just alphanumeric)
CLASSIC_B64_REGEX = re.compile(r"[A-Za-z0-9+/=]{30,}")

# URL-safe Base64: [A-Za-z0-9\-_], no +/=
URLSAFE_B64_REGEX = re.compile(r"[A-Za-z0-9\-_]{40,}")

# ── Helper ────────────────────────────────────────


def _has_mixed_case(s: str) -> bool:
    """Real Base64 always has both upper and lowercase."""
    return bool(re.search(r"[A-Z]", s)) and bool(re.search(r"[a-z]", s))


def _alphabet_size(s: str) -> int:
    """Count unique characters in base64 alphabet."""
    b64_chars = {c for c in s if c.isalnum() or c in "+/=-_"}
    return len(b64_chars)


def _has_base64_signal(s: str) -> bool:
    """Real Base64 has + or / chars - pure alphanumeric is not Base64."""
    return bool(re.search(r"[+/]", s)) and _has_mixed_case(s)


# ── Scoring Model ─────────────────────────────────


def base64_score(raw: str) -> float:
    """
    Analyst scoring: how Base64-like is this path?

    0.0 = no signals
    0.7+ = classic Base64 with mixed case
    0.9+ = JWT/Laravel encrypted token (eyJ prefix)

    Signals:
        +0.9  JWT/Laravel prefix (eyJ...)
        +0.7  classic Base64 (mixed case, 40+ chars)
        +0.3  high alphabet diversity (>30 unique chars)
    """
    s = raw.strip()
    val = 0.0

    # JWT/Laravel: strongest signal - encrypted JSON payload
    if JWT_REGEX.search(s):
        val += 0.9

    # Classic Base64: long mixed-case string with + / = chars
    m = CLASSIC_B64_REGEX.search(s)
    if m:
        token = m.group()
        if _has_base64_signal(token):
            val += 0.7

    # Alphabet diversity bonus
    if val > 0.0 and _alphabet_size(s) > 30:
        val += 0.3

    return min(val, 1.0)


# ── Type Detection ────────────────────────────────


def detect_type(raw: str) -> str:
    """
    Returns: "jwt" | "classic" | "none"
    """
    if JWT_REGEX.search(raw):
        return "jwt"

    m = CLASSIC_B64_REGEX.search(raw)
    if m and _has_base64_signal(m.group()):
        return "classic"

    return "none"


# ── Context ───────────────────────────────────────


def is_in_query(raw: str) -> bool:
    """Base64 token is in a query string."""
    return "?" in raw and "=" in raw


# ── Full Analysis ─────────────────────────────────


def analyze(raw: str) -> dict:
    """Full base64 analysis for a path token."""
    score = base64_score(raw)
    bt = detect_type(raw)
    return {
        "base64_score": score,
        "base64_type": bt,
        "is_in_query": is_in_query(raw),
        "classification_hint": "api"
        if score > 0.5
        else ("search" if is_in_query(raw) else None),
    }


# ── Unified Identifier Scores (all 4 types) ──────


def identifier_type_scores(raw: str) -> dict[str, float]:
    """Compare all four identifier types: uuid, timestamp, hash, base64."""
    scores = {"uuid": 0.0, "timestamp": 0.0, "hash": 0.0, "base64": base64_score(raw)}
    try:
        from researchs.uuid.detector import uuid_score

        scores["uuid"] = uuid_score(raw)
    except ImportError:
        pass
    try:
        from researchs.timestamps.detector import timestamp_score

        scores["timestamp"] = timestamp_score(raw)
    except ImportError:
        pass
    try:
        from researchs.hash.detector import hash_score

        scores["hash"] = hash_score(raw)
    except ImportError:
        pass
    return scores


# ── Demo ──────────────────────────────────────────

if __name__ == "__main__":
    samples = [
        "eyJpdiI6Ii9CVlVOWkcyeWFxVWY2d3BqSVh6dHc9PSIsInZhbHVlIjoiVkZFSzAxVU1ua1ZxUlFja0s0MFAydFhZUWtzZnFVVzJq",
        "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXo=",
        "panduan-belajar-online",
        "9e107d9d372bb6826bd81d3542a419d6",
        "dXNlcl9pZD0xMjM0JnJlZGlyZWN0PS9ob21l",
    ]

    print(f"{'PATH':<60} {'SCORE':>6} {'TYPE':>8} {'-> HINT'}")
    print("-" * 85)
    for raw in samples:
        a = analyze(raw)
        print(
            f"{raw[:58]:<60} {a['base64_score']:>6.2f} {a['base64_type']:>8}  -> {a['classification_hint'] or '-'}"
        )
