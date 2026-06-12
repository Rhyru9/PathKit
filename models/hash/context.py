"""
context.py - Hash type detection, bundler chunk, and embedded detection.
"""

import re

from .constants import (
    BUNDLER_CHUNK_REGEX,
    GENERIC_HEX_REGEX,
    MD5_REGEX,
    SHA1_REGEX,
    SHA256_REGEX,
    TRUNCATED_HEX_REGEX,
    UUID_LIKE_REGEX,
)


def detect_type(raw: str) -> str:
    """
    Identify the dominant hash type.

    Returns: "sha256" | "sha1" | "md5" | "truncated" | "generic" | "none"
    """
    if UUID_LIKE_REGEX.search(raw):
        return "none"
    if SHA256_REGEX.search(raw):
        return "sha256"
    if SHA1_REGEX.search(raw):
        return "sha1"
    if MD5_REGEX.search(raw):
        return "md5"
    if TRUNCATED_HEX_REGEX.search(raw):
        return "truncated"
    if GENERIC_HEX_REGEX.search(raw):
        return "generic"
    return "none"


def is_bundler_chunk(raw: str) -> bool:
    """
    Bundler artifact: <hash>.js/.css/.map
    /chunk/2441aee32022b479.js -> True
    """
    return bool(BUNDLER_CHUNK_REGEX.search(raw))


def is_hash_embedded(raw: str) -> bool:
    """
    Hash mixed with readable tokens in the SAME path segment.
    /article/9e107d9d-panduan -> True  (CMS hybrid leak)
    /file/a94a8fe...         -> False (path prefix, hash is isolated)
    """
    if detect_type(raw) == "none":
        return False
    segments = re.split(r"[/]", raw.lower())
    for seg in segments:
        if GENERIC_HEX_REGEX.search(seg) or TRUNCATED_HEX_REGEX.search(seg):
            toks = re.split(r"[-_]", seg)
            readable = [t for t in toks if t.isalpha() and len(t) >= 3]
            if readable:
                return True
    return False
