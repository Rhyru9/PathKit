"""Canonical PathKit classification flow shared by CLI, evaluation, and ablation."""

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


# Detector stage names that can be toggled off for ablation studies.
DETECTOR_STAGES = frozenset(
    {"encoding", "search", "uuid", "timestamp", "hash", "base64", "other", "ml"}
)


def classify_path(
    raw: str,
    model: URLIntentModel,
    fallback_label: str | None = None,
    disabled: frozenset[str] | None = None,
) -> Classification:
    """
    Apply the production detector priority and return one auditable result.

    Args:
        fallback_label: if set, returned instead of consulting the ML model
            (used by the rule-only baseline to isolate detector contribution).
        disabled: a set of DETECTOR_STAGES to skip (used by ablation studies).
            The ML classifier is consulted last; disabling "ml" makes the final
            fallback return `fallback_label` (or the ML result if not disabled).
    """
    disabled = frozenset(disabled or ())
    unknown = disabled - DETECTOR_STAGES
    if unknown:
        raise ValueError(
            f"Unknown disabled detector stage(s): {', '.join(sorted(unknown))}"
        )
    decoded = decode(raw)
    path = decoded.split("?", 1)[0]

    # 1. Encoding detector (=XX routing escapes)
    if "encoding" not in disabled:
        raw_path = raw.split("?", 1)[0]
        if re.search(r"(?:=|%3[dD])(?:3[aA]|2[eE]|5[fF]|3[dD])", raw_path):
            return Classification("encoded", "encoding", 1.0, decoded)

    # 2. Search detector (query string)
    if "search" not in disabled and "?" in decoded and "=" in decoded:
        return Classification("search", "query", 1.0, decoded)

    from .uuid import score as uuid_score
    from .uuid import detect as uuid_context
    from .timestamp import detect_type as timestamp_type
    from .timestamp import is_hybrid_slug
    from .timestamp import score as timestamp_score
    from .hash import is_bundler_chunk, is_hash_embedded
    from .hash import score as hash_score
    from .base64 import score as base64_score
    from .other import classify as other_classify
    from .other import score as other_score

    # 3. UUID detector
    if "uuid" not in disabled and uuid_score(raw) > 0.5:
        context = uuid_context(raw)
        label = {"asset": "asset", "query": "search"}.get(context, "random_id")
        return Classification(label, "uuid", uuid_score(raw), decoded)

    # 4. Timestamp detector
    if "timestamp" not in disabled and timestamp_score(raw) > 0.5:
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

    # 5. Hash detector
    if "hash" not in disabled and hash_score(raw) > 0.5:
        if is_bundler_chunk(raw):
            label = "asset"
        elif is_hash_embedded(raw):
            label = "random_id"
        elif "?" in raw:
            label = "search"
        else:
            label = "api"
        return Classification(label, "hash", hash_score(raw), decoded)

    # 6. Base64 detector
    if "base64" not in disabled and base64_score(raw) > 0.5:
        label = "search" if "?" in raw else "api"
        return Classification(label, "base64", base64_score(raw), decoded)

    # 7. Other (routing / ID / file-ext) detector
    if "other" not in disabled:
        other_score_value = other_score(raw)
        if other_score_value > 0.5:
            label = other_classify(raw) or "random_id"
            return Classification(label, "other", other_score_value, decoded)

    # 8. ML classifier (or fallback)
    if fallback_label is not None:
        return Classification(fallback_label, "fallback", 1.0, decoded)

    if "ml" in disabled:
        raise ValueError("Disabling 'ml' requires a fallback_label")

    result = model.predict(raw)
    return Classification(result["final"], "slug_model", result["confidence"], decoded)
