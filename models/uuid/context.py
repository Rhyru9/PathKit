"""
context.py - UUID context classification (what the path IS, not just format).
"""

import re

from .constants import UUID_REGEX


def detect(raw: str) -> str:
    """
    Detect UUID context in a path token.

    Returns one of: "standalone" | "embedded" | "asset" | "query" | "none"

        standalone  - entire string is a UUID -> API/object endpoint
        embedded    - UUID inside larger text -> CMS hybrid (bad slug)
        asset       - UUID + file extension -> CDN/storage
        query       - UUID in query params -> search/API fetch
        none        - no UUID detected
    """
    s = raw.strip().lower()

    if not UUID_REGEX.search(s):
        return "none"

    # Asset: UUID + file extension
    if re.search(r"\.(js|css|png|jpg|jpeg|gif|svg|webp|pdf|json|xml|php)$", s):
        return "asset"

    # Query: UUID in query params
    if "?" in s and "=" in s:
        return "query"

    # Standalone: entire string is UUID
    if UUID_REGEX.fullmatch(s):
        return "standalone"

    # Embedded: UUID inside larger text (CMS hybrid)
    return "embedded"
