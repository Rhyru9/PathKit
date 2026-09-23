"""
constants.py - Encoding patterns and type labels.
"""

import re
from enum import Enum


class EncodingType(str, Enum):
    ASCII = "ascii"          # plain text, no encoding
    URLENCODE = "urlencode"   # %XX percent-encoding
    HEX = "hex"               # =XX in-path hex-encoding (after url-decode)
    BASE64 = "base64"         # base64 / JWT (eyJ...)
    UNICODE = "unicode"       # \\uXXXX escapes or non-ASCII
    DOUBLE = "double"         # double-encoded (e.g. %25XX)


# %XX percent-encoding
URL_ENCODE_RE = re.compile(r"%[0-9A-Fa-f]{2}")

# Double-encoded percent: %25XX (%25 -> %)
DOUBLE_ENCODE_RE = re.compile(r"%25[0-9A-Fa-f]{2}")

# =XX in-path hex encoding (=5F -> _, =3A -> :, =2E -> .)
HEX_ENCODE_RE = re.compile(r"=([0-9A-Fa-f]{2})")

# Base64 / JWT prefix
JWT_RE = re.compile(r"eyJ[A-Za-z0-9+/=]{20,}")

# Unicode escape \\uXXXX
UNICODE_ESCAPE_RE = re.compile(r"\\u[0-9A-Fa-f]{4}")

# Non-ASCII characters (CJK, accented, emoji, etc.)
NON_ASCII_RE = re.compile(r"[^\x00-\x7F]")
