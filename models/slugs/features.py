"""
features.py - Feature extraction pipeline for URL path tokens.
"""

import math
import re
from collections import Counter

from .constants import (
    ANTI_SLUG_WORDS,
    COMMON_WORDS,
    MAX_ANTI_HITS,
    MAX_AVG_TOKEN_LEN,
    MAX_COMMON_HITS,
    MAX_ENTROPY,
    MAX_LEN_NORM,
    MAX_READABLE_COUNT,
    MAX_TOKEN_COUNT,
    VOWELS,
)


def _entropy(s: str) -> float:
    """Shannon entropy of a string (normalized)."""
    if not s:
        return 0.0
    freq = Counter(s)
    L = len(s)
    return -sum((c / L) * math.log2(c / L) for c in freq.values())


def _url_decode(raw: str) -> str:
    """Decode percent-encoded path tokens."""
    return re.sub(
        r"%([0-9A-Fa-f]{2})",
        lambda m: chr(int(m.group(1), 16)),
        raw.strip(),
    )


def extract(raw: str) -> dict:
    """Extract normalized feature vector from a raw URL path token."""
    decoded = _url_decode(raw)
    s = decoded.lower()
    f: dict = {}

    # -- Structural features (0.0-1.0) --
    f["len_norm"] = min(len(s), int(MAX_LEN_NORM)) / MAX_LEN_NORM
    f["has_dash"] = 1.0 if "-" in s else 0.0
    f["has_underscore"] = 1.0 if "_" in s else 0.0
    f["has_dot"] = 1.0 if "." in s else 0.0
    f["has_slash"] = 1.0 if "/" in s else 0.0

    # ── Density features ──
    f["dash_ratio"] = s.count("-") / max(len(s), 1)
    f["digit_ratio"] = sum(c.isdigit() for c in s) / max(len(s), 1)

    # ── Entropy ──
    f["entropy_norm"] = _entropy(s) / MAX_ENTROPY

    # ── Linguistic features ──
    alphas = [c for c in s if c.isalpha()]
    if alphas:
        vowels = sum(1 for c in alphas if c in VOWELS)
        f["vowel_ratio"] = vowels / len(alphas)
    else:
        f["vowel_ratio"] = 0.0

    # Gibberish: 4+ consecutive non-vowel consonants
    f["has_gibberish"] = 1.0 if re.search(r"[^aeiou0-9\-_/.\s]{4,}", s) else 0.0

    # ── Token features ──
    toks = re.split(r"[-_/.\s]+", s)
    toks = [t for t in toks if t]
    f["token_count_norm"] = min(len(toks), int(MAX_TOKEN_COUNT)) / MAX_TOKEN_COUNT
    f["avg_token_len_norm"] = (
        sum(len(t) for t in toks) / max(len(toks), 1)
    ) / MAX_AVG_TOKEN_LEN

    # Readable tokens
    readable = [t for t in toks if t.isalpha() and len(t) >= 3]
    f["readable_count_norm"] = min(len(readable), MAX_READABLE_COUNT) / float(
        MAX_READABLE_COUNT
    )

    # Stopword / common word hits
    common_hits = sum(1 for t in toks if t in COMMON_WORDS)
    f["common_word_hits"] = min(common_hits, MAX_COMMON_HITS) / float(MAX_COMMON_HITS)

    # Anti-slug hits
    anti_hits = sum(1 for t in toks if t in ANTI_SLUG_WORDS)
    f["anti_slug_hits"] = min(anti_hits, MAX_ANTI_HITS) / float(MAX_ANTI_HITS)

    # Average per-token entropy
    if toks:
        tok_entropies = [_entropy(t) for t in toks]
        f["token_entropy_norm"] = (
            sum(tok_entropies) / len(tok_entropies)
        ) / MAX_ENTROPY
    else:
        f["token_entropy_norm"] = 0.0

    # ── Pattern flags ──
    f["is_hex"] = 1.0 if re.match(r"^[a-f0-9]+$", s) and len(s) >= 8 else 0.0
    f["is_uuid"] = (
        1.0
        if re.match(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", s
        )
        else 0.0
    )
    f["is_file_ext"] = (
        1.0 if re.search(r"\.(js|css|php|html|json|xml|pdf|sql|env|bak)$", s) else 0.0
    )
    f["is_catalog"] = 1.0 if re.search(r"=3[aA]|=2[eE]", s) else 0.0
    f["has_special"] = 1.0 if re.search(r"[%{}\[\]<>]", s) else 0.0
    f["is_noise"] = (
        1.0
        if (f["has_special"] and not f["has_dash"] and f["len_norm"] < 0.15)
        else 0.0
    )

    if toks:
        f["first_is_num"] = 1.0 if toks[0].isdigit() else 0.0
    else:
        f["first_is_num"] = 0.0

    return f
