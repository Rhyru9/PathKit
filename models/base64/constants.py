"""
constants.py - Base64 patterns, scoring weights, and context labels.
"""

import re

# ── Patterns ──────────────────────────────────────

# JWT/Laravel: eyJ = Base64 of '{'
JWT_REGEX = re.compile(r"eyJ[A-Za-z0-9+/=]{40,}")

# Classic Base64: must contain + or / (not just alphanumeric)
CLASSIC_B64_REGEX = re.compile(r"[A-Za-z0-9+/=]{30,}")

# ── Scoring weights ───────────────────────────────

SCORE_JWT = 0.9
SCORE_CLASSIC = 0.7
SCORE_DIVERSITY_BONUS = 0.3
DIVERSITY_THRESHOLD = 30

# ── Context labels ────────────────────────────────

CONTEXT_CLASSES = {
    "jwt": "api",  # Laravel session/CSRF token
    "classic": "api",  # Classic base64 (auth/encoded data)
}
