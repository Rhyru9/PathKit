"""
pii_rules.py — Canonical PII detection + redaction rules.

Single source of truth shared by audit_pii.py and sanitize_dataset.py so the
two can never diverge. Order matters: credentials are detected BEFORE emails.
"""

import re
from urllib.parse import unquote

# ── Decode ─────────────────────────────────────────


def decode(s: str) -> str:
    """
    Percent-decode with proper UTF-8 handling. `unquote` correctly decodes
    multi-byte UTF-8 sequences (e.g. %E2%9C%A8 -> U+2728), unlike a naive
    per-byte chr(int(...)) which would emit mojibake.
    """
    return unquote(s, encoding="utf-8", errors="replace")


# ── Detection patterns (single source of truth) ────

# 1. Credential: login:<email>:<password>  (detect BEFORE email)
CRED_RE = re.compile(r"login:[^:\s/]+:[^:\s/]+", re.IGNORECASE)

# 2. Email (standalone OR embedded)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

# 3. NIP + name: <12-16 digits>-<Name> (as a path segment).
#    Leading ^|/ is captured (not lookbehind) so re.sub preserves structure.
NIP_NAME_RE = re.compile(r"(^|/)\d{12,16}-[A-Za-z][^/]*")

# 4. ID code: <letter><5-8 digits> (as a full path segment)
ID_CODE_RE = re.compile(r"(^|/)[A-Za-z]\d{5,8}(?=/|$)")

# 5. Phone: +62... or 08...
PHONE_RE = re.compile(r"(?:\+62\d{8,12}|\b08\d{8,12}\b)")

# 6. Encoded author name: =3A (colon) / =2E (period) ONLY within a
#    /creators/ route (EPrints "Family=3AGiven=2EInitials"). Excludes
#    /subjects/ (topical terms) and other =3A/=2E uses that are NOT PII.
AUTHOR_NAME_RE = re.compile(r"(/creators/)[^/]*=(?:3[Aa]|2[Ee])[^/]*")

# ── Rules table (name, detect_re, severity) ────────

RULES = [
    ("credential", CRED_RE, "critical"),
    ("email", EMAIL_RE, "high"),
    ("nip_name", NIP_NAME_RE, "high"),
    ("id_code", ID_CODE_RE, "high"),
    ("phone", PHONE_RE, "high"),
    ("encoded_name", AUTHOR_NAME_RE, "medium"),
]


def detect_all(text: str) -> set[str]:
    """Return the set of PII types present in a (decoded) string."""
    return {name for name, rx, _ in RULES if rx.search(text)}


def redact_token(token: str) -> tuple[str, str | None]:
    """
    Redact PII in a single token (or endpoint string).
    Returns (redacted, type) where type is the redaction applied, or None.
    The FIRST matching rule wins (credential before email).
    Decodes first so percent-encoded PII is visible to the patterns.
    """
    token = decode(token)

    # 1. Credential -> drop the whole token
    if CRED_RE.search(token):
        return "", "credential"

    # 2. Email -> redact every occurrence, preserve surrounding structure
    if EMAIL_RE.search(token):
        return EMAIL_RE.sub("[EMAIL]", token), "email"

    # 3. NIP + name -> redact the segment, preserve leading slash
    if NIP_NAME_RE.search(token):
        return NIP_NAME_RE.sub(r"\1[NIP_NAME]", token), "nip_name"

    # 4. ID code -> redact the segment, preserve leading slash
    if ID_CODE_RE.search(token):
        return ID_CODE_RE.sub(r"\1[ID_CODE]", token), "id_code"

    # 5. Phone -> redact every occurrence
    if PHONE_RE.search(token):
        return PHONE_RE.sub("[PHONE]", token), "phone"

    # 6. Encoded author name -> redact the name segment, keep route structure
    if AUTHOR_NAME_RE.search(token):
        return AUTHOR_NAME_RE.sub(lambda m: m.group(1) + "[NAME]", token), "encoded_name"

    return token, None
