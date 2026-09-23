"""
constants.py - "Other" patterns, scoring weights, and context labels.

"Other" = catch-all for artifacts that are not slugs and not caught by the
dedicated identifiers (uuid/timestamp/hash/base64). Includes internal routing
codes, opaque identifiers, and file/asset extensions (resolved by rule BEFORE
the ML slug classifier).
"""

import re

# ── Patterns ──────────────────────────────────────

# Org unit chain: ditjen=5Fbudaya=5Fsesditjen=5Fupt26
ORG_UNIT_REGEX = re.compile(r"(?:[a-z]+=5F){2,}[a-z0-9]+", re.IGNORECASE)

# Dotted version (2+ dots): PED003.3.4, KR03.005.03
DOTTED_VERSION_REGEX = re.compile(
    r"\b[A-Z]{2,5}\d{2,4}\.\d{1,3}\.\d{1,3}", re.IGNORECASE
)

# Single-dot version: PED001.3, PED000.21
VERSION_1DOT_REGEX = re.compile(r"^[A-Za-z]{2,5}\d{2,4}\.\d{1,3}$")

# Short pure numeric ID: 5-10 digits (not a timestamp range)
SHORT_NUMERIC_REGEX = re.compile(r"^\d{5,10}$")

# Letter + digits ID code: P9996589, K5651679
ID_CODE_REGEX = re.compile(r"^[A-Za-z]\d{5,8}$")

# Random mixed-case alphanumeric: vDnPZwVN0j, x50WB2gm9Z (5-12 chars)
RANDOM_ALNUM_REGEX = re.compile(r"^[A-Za-z0-9]{5,12}$")

# Number + dash + number/hex: 8253-2, 14061-39bbd0a (ID + sub-ID)
NUM_DASH_REGEX = re.compile(r"^\d+-[0-9a-f]+$", re.IGNORECASE)

# Static web asset extensions: .js, .css, .map
ASSET_EXT_REGEX = re.compile(r"\.(js|css|map)$", re.IGNORECASE)

# Document / data file extensions (everything that is NOT a slug)
FILE_EXT_REGEX = re.compile(
    r"\.(xml|html?|json|pdf|csv|tsv|txt|n3|nt|rdf|ris|bib|enw|refer|rss|"
    r"docx?|xlsx?|pptx?|odt|ods|php|asp|aspx|jsp|sql|env|bak|config|ya?ml)$",
    re.IGNORECASE,
)

# ── Scoring weights ───────────────────────────────

SCORE_ORG_UNIT = 0.8
SCORE_DOTTED_VERSION = 0.7
SCORE_VERSION_1DOT = 0.7
SCORE_NUMERIC_ID = 0.5
SCORE_ID_CODE = 0.8
SCORE_RANDOM_ALNUM = 0.7
SCORE_NUM_DASH = 0.7
SCORE_ASSET_EXT = 0.8
SCORE_FILE_EXT = 0.8

# ── Context labels ────────────────────────────────

CONTEXT_CLASSES = {
    "org_unit": "encoded",         # hex-encoded routing ( =5F delimiters )
    "dotted_version": "random_id",  # versioned document reference
    "version_1dot": "random_id",    # single-dot version
    "numeric_id": "random_id",      # pure numeric identifier
    "id_code": "random_id",         # letter+digits ID
    "random_alnum": "random_id",    # random mixed-case token
    "num_dash": "random_id",        # number + dash + number/hex
    "static_asset": "asset",        # .js/.css/.map static file
    "file_ext": "file",             # document/data file
}
