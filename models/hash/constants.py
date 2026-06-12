"""
constants.py - Hash patterns, scoring weights, and context labels.
"""

import re

# ── Hash patterns ─────────────────────────────────

MD5_REGEX = re.compile(r"\b[a-f0-9]{32}\b", re.IGNORECASE)
SHA1_REGEX = re.compile(r"\b[a-f0-9]{40}\b", re.IGNORECASE)
SHA256_REGEX = re.compile(r"\b[a-f0-9]{64}\b", re.IGNORECASE)
GENERIC_HEX_REGEX = re.compile(r"\b[a-f0-9]{24,128}\b", re.IGNORECASE)

# Truncated: must contain at least one hex letter [a-f], not just digits
TRUNCATED_HEX_REGEX = re.compile(r"\b(?=[a-f0-9]*[a-f])[a-f0-9]{8,16}\b", re.IGNORECASE)

# Bundler chunk: <hash>.js/.css/.map (8-32 hex chars)
BUNDLER_CHUNK_REGEX = re.compile(r"[a-f0-9]{8,32}\.(js|css|map)$", re.IGNORECASE)

# UUID pattern - skip these (owned by models.uuid)
UUID_LIKE_REGEX = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)

# ── Scoring weights ───────────────────────────────

SCORE_SHA256 = 0.9
SCORE_SHA1 = 0.85
SCORE_MD5 = 0.8
SCORE_GENERIC = 0.6
SCORE_TRUNCATED = 0.3
SCORE_DIVERSITY_BONUS = 0.2
DIVERSITY_THRESHOLD = 0.5

# ── Context labels ────────────────────────────────

CONTEXT_CLASSES = {
    "sha256": "asset",  # modern CDN / S3
    "sha1": "api",  # git / tokens
    "md5": "api",  # legacy CDN / integrity
    "truncated": "asset",  # bundler chunks
    "generic": "api",  # unknown long hex
}
