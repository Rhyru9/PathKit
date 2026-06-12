"""
labeling.py - Heuristic auto-labeling for self-supervised slug classification.
"""

import re

from .constants import COMMON_WORDS


def _url_decode(raw: str) -> str:
    """Decode percent-encoded path tokens."""
    return re.sub(
        r"%([0-9A-Fa-f]{2})",
        lambda m: chr(int(m.group(1), 16)),
        raw.strip(),
    )


def auto_label(raw: str) -> str | None:
    """
    Heuristically label a raw URL path token.
    Returns None if no confident rule applies (-> used as negative example).
    """
    decoded = _url_decode(raw)
    s = decoded.lower()

    # ── Reject: special-char-heavy noise ──
    if re.search(r"[%{}\[\]<>]", s) and len(s) < 30:
        return None

    # ── Strong random_id signals ──
    if re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", s):
        return "random_id"
    if re.match(r"^[0-9a-f]{32}$", s):
        return "random_id"
    if re.match(r"^[a-f0-9]{24,64}$", s):
        return "random_id"
    if re.match(r"^1[0-9]{9}$", s):
        return "random_id"
    if re.match(r"^(19|20)\d{6}$", s):
        return "random_id"

    # ── Strong encoded signals ──
    if re.search(r"=3[aA]|=2[eE]", s):
        return "encoded"
    if re.search(r"[^:]+@[^:]+\.[^:]+:[^:]+", s):
        return "encoded"

    # ── Strong asset signals ──
    if re.search(r"\.(js|css)$", s) and re.search(r"[a-f0-9]{8,20}", s):
        return "asset"

    # ── Strong file signals ──
    if re.search(r"\.(php|asp|jsp|sql|env|bak|config|yml)$", s):
        return "file"
    if re.search(r"\.(html|json|xml|pdf)$", s):
        return "file"

    # ── API signals ──
    if re.search(r"/api/|/rest/|/graphql", s):
        return "api"

    # ── Search signals ──
    if "?" in s and "=" in s:
        return "search"

    # ── Slug signals ──
    toks = re.split(r"[-_/.\s]+", s)
    toks = [t for t in toks if t]
    readable = [t for t in toks if t.isalpha() and len(t) >= 3]
    common_hits = sum(1 for t in toks if t in COMMON_WORDS)

    if len(readable) >= 2 or common_hits >= 1:
        return "slug"

    # Numeric slug: 123-post-title (but NOT UUID-like)
    if re.match(r"^\d{3,}-[a-z]", s) and not re.match(r"^\d{8}-[0-9a-f]{4}", s):
        return "slug"

    return None
