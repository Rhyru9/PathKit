"""
other/detector.py - Catch-all non-slug detector for internal routing artifacts.

These are NOT identifiers (uuid/timestamp/hash/base64) and NOT slugs.
They are internal routing codes, versioned references, org unit IDs.
"""

import re

# ── Patterns ──────────────────────────────────────

# Encoded delimiters: =5F (_), =3D (=), =2E (.)
ENCODED_DELIM_REGEX = re.compile(r"=[0-9A-Fa-f]{2}")

# Dotted version: PREFIX###.###.###
DOTTED_VERSION_REGEX = re.compile(
    r"\b[A-Z]{2,5}\d{2,4}\.\d{1,3}\.\d{1,3}", re.IGNORECASE
)

# Short pure numeric ID: 5-10 digits, not a timestamp range
SHORT_NUMERIC_REGEX = re.compile(r"^\d{5,10}$")

# Org unit chain: multiple =5F segments
ORG_UNIT_REGEX = re.compile(r"(?:[a-z]+=5F){2,}[a-z0-9]+", re.IGNORECASE)


# ── Scoring ───────────────────────────────────────


def other_score(raw: str) -> float:
    """
    Catch-all for internal routing / system artifacts that are not slugs.

    Signals:
        +0.8  org unit chain (3+ =5F segments)
        +0.7  dotted version path (PED003.3.4)
        +0.5  short pure numeric ID (5-10 digits, not a timestamp)
    """
    s = raw.strip()
    val = 0.0

    # Org unit chain: ditjen=5Fbudaya=5Fseditjen=5Fupt26
    if ORG_UNIT_REGEX.search(s):
        val += 0.8

    # Dotted version path
    if DOTTED_VERSION_REGEX.search(s):
        val += 0.7

    # Short pure numeric ID
    if SHORT_NUMERIC_REGEX.match(s):
        val += 0.5

    return min(val, 1.0)


# ── Type Detection ────────────────────────────────


def detect_type(raw: str) -> str:
    """
    Returns: "org_unit" | "dotted_version" | "numeric_id" | "none"
    """
    if ORG_UNIT_REGEX.search(raw):
        return "org_unit"
    if DOTTED_VERSION_REGEX.search(raw):
        return "dotted_version"
    if SHORT_NUMERIC_REGEX.match(raw):
        return "numeric_id"
    return "none"


# ── Unified catch-all ─────────────────────────────


def is_non_slug_system_artifact(raw: str) -> bool:
    """
    True if this path is clearly a system artifact, not a slug.
    Integrates ALL identifier detectors for a unified rejection check.
    """
    # Try all detectors
    scores = {}

    # Other (us)
    scores["other"] = other_score(raw)

    # UUID
    try:
        from researchs.uuid.detector import uuid_score

        scores["uuid"] = uuid_score(raw)
    except ImportError:
        scores["uuid"] = 0.0

    # Timestamp
    try:
        from researchs.timestamps.detector import timestamp_score

        scores["timestamp"] = timestamp_score(raw)
    except ImportError:
        scores["timestamp"] = 0.0

    # Hash
    try:
        from researchs.hash.detector import hash_score

        scores["hash"] = hash_score(raw)
    except ImportError:
        scores["hash"] = 0.0

    # Base64
    try:
        from researchs.base64.detector import base64_score

        scores["base64"] = base64_score(raw)
    except ImportError:
        scores["base64"] = 0.0

    return any(v > 0.5 for v in scores.values())


# ── Full Analysis ─────────────────────────────────


def analyze(raw: str) -> dict:
    """Full analysis with all identifier scores."""
    s = raw.strip()
    return {
        "other_score": other_score(s),
        "other_type": detect_type(s),
        "is_system_artifact": is_non_slug_system_artifact(raw),
    }


# ── Demo ──────────────────────────────────────────

if __name__ == "__main__":
    samples = [
        "ditjen=5Fbudaya=5Fsesditjen=5Fupt26",  # org unit
        "PED003.3.4",  # dotted version
        "70032380",  # numeric ID
        "panduan-belajar-online",  # slug
        "ditjen=5Fdikdasmen=5Fsd",  # org unit
        "9e107d9d372bb6826bd81d3542a419d6",  # hash (not other)
    ]

    print(f"{'PATH':<48} {'OTHER':>6} {'TYPE':>16} {'ARTIFACT':>9}")
    print("-" * 85)
    for raw in samples:
        a = analyze(raw)
        print(
            f"{raw[:46]:<48} {a['other_score']:>6.2f} "
            f"{a['other_type']:>16} "
            f"{str(a['is_system_artifact']):>9}"
        )
