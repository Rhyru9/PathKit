"""
constants.py - UUID patterns, context labels, and scoring configuration.
"""

import re

# ── UUID Pattern (RFC 4122): 8-4-4-4-12 ──────────

UUID_REGEX = re.compile(
    r"[0-9a-fA-F]{8}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{12}"
)

UUID_LOOSE_REGEX = re.compile(r"[0-9a-fA-F]{8,}-[0-9a-fA-F]{4,}-[0-9a-fA-F]{4,}")

# ── Scoring weights ───────────────────────────────

SCORE_PARTIAL = 0.4  # long hex-dash substring present
SCORE_FULL = 0.9  # strict full-match UUID
SCORE_DASH_COUNT = 0.2  # exactly 4 dashes (structural hyphens)
PENALTY_NON_HEX = -0.5  # non-hex alpha chars (g-z, G-Z)

# ── Context labels ────────────────────────────────

CONTEXT_CLASSES = {
    "standalone": "random_id",  # UUID alone -> API/object endpoint
    "embedded": "review",  # UUID in text -> CMS hybrid, bad slug
    "asset": "asset",  # UUID + file extension -> CDN storage
    "query": "search",  # UUID + ?= -> search/API fetch
}
