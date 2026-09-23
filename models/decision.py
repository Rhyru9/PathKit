"""Canonical PathKit classification flow shared by CLI and evaluation."""

import re
from dataclasses import dataclass

from .encoding import decode
from .slugs import URLIntentModel


@dataclass(frozen=True)
class Classification:
    label: str
    detector: str
    confidence: float
    decoded: str


def classify_path(raw: str, model: URLIntentModel) -> Classification:
    """Apply the production detector priority and return one auditable result."""
    decoded = decode(raw)
    path = decoded.split("?", 1)[0]

    # These are routing escapes, not ordinary URL encoding or query values.
    raw_path = raw.split("?", 1)[0]
    if re.search(
        r"(?:=|%3[dD])(?:3[aA]|2[eE]|5[fF]|3[dD])", raw_path
    ):
        return Classification("encoded", "encoding", 1.0, decoded)

    if "?" in decoded and "=" in decoded:
        return Classification("search", "query", 1.0, decoded)

    from .uuid import score as uuid_score
    from .uuid import detect as uuid_context
    from .timestamp import detect_type as timestamp_type
    from .timestamp import is_hybrid_slug
    from .timestamp import score as timestamp_score
    from .hash import detect_type as hash_type
    from .hash import is_bundler_chunk, is_hash_embedded
    from .hash import score as hash_score
    from .base64 import detect_type as base64_type
    from .base64 import score as base64_score
    from .other import classify as other_classify
    from .other import score as other_score

    if uuid_score(raw) > 0.5:
        context = uuid_context(raw)
        label = {"asset": "asset", "query": "search"}.get(context, "random_id")
        return Classification(label, "uuid", uuid_score(raw), decoded)

    if timestamp_score(raw) > 0.5:
        kind = timestamp_type(raw)
        if kind == "date_path" and is_hybrid_slug(path):
            label = "slug"
        elif kind == "date_path":
            label = "search"
        elif kind == "iso_date":
            label = "file"
        else:
            label = "api"
        return Classification(label, "timestamp", timestamp_score(raw), decoded)

    if hash_score(raw) > 0.5:
        if is_bundler_chunk(raw):
            label = "asset"
        elif is_hash_embedded(raw):
            label = "random_id"
        elif "?" in raw:
            label = "search"
        else:
            label = "api"
        return Classification(label, "hash", hash_score(raw), decoded)

    if base64_score(raw) > 0.5:
        label = "search" if "?" in raw else "api"
        return Classification(label, "base64", base64_score(raw), decoded)

    other_score_value = other_score(raw)
    if other_score_value > 0.5:
        label = other_classify(raw) or "random_id"
        return Classification(label, "other", other_score_value, decoded)

    result = model.predict(raw)
    return Classification(
        result["final"], "slug_model", result["confidence"], decoded
    )
