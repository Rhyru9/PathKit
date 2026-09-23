#!/usr/bin/env python3
"""
label_clean_test.py — First-pass (Annotator A) labeling of the clean test set.

Fills the `label_a` column of data/annotate/clean_test.csv using semantic
rules (7-class taxonomy). This is a FIRST PASS for demonstration — a second,
independent human annotator must fill `label_b` separately for a valid
Cohen's kappa.

Usage:
    python scripts/label_clean_test.py
"""

import csv
import re
import sys
from pathlib import Path
from urllib.parse import unquote

PROJECT_ROOT = Path(__file__).resolve().parent.parent

VALID = {"slug", "api", "asset", "search", "random_id", "file", "encoded"}

UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE)
HEX_RE = re.compile(r"\b[a-f0-9]{32}\b", re.IGNORECASE)


def label(raw: str) -> str:
    """Assign one of the 7 classes to a full endpoint/path token."""
    decoded = unquote(raw, errors="replace")
    s = decoded.lower()

    # 1. Encoded: heavy percent/hex encoding (beyond ordinary %20 spaces)
    if (
        re.search(r"%(?!20|2f|2d|3a|2e)[0-9a-f]{2}", s)
        or (re.search(r"=[0-9a-f]{2}(?:[^0-9a-f]|$)", s) and "?" not in s)
    ):
        return "encoded"

    # 2. Search: query string with ? and =
    if "?" in s and "=" in s:
        return "search"

    # 3. API: programmatic/object endpoint patterns
    if re.search(r"/api/|/rest/|/graphql|/cgi/|/npsn/|/data-induk/|/id/eprint/|/profil|/export/", s):
        return "api"

    # 4. Asset: static web files
    if re.search(r"\.(js|css|map)(\?|$)", s):
        return "asset"

    # 5. File: document/download extensions
    if re.search(r"\.(pdf|xml|html?|txt|csv|json|n3|nt|rdf|ris|bib|enw|refer|docx?|xlsx?|php|asp|jsp)(\?|$)", s):
        return "file"

    # 6. Random ID: UUID, hash, ID code, pure-numeric object segment
    if UUID_RE.search(s) or HEX_RE.search(s):
        return "random_id"
    if re.search(r"/(\d{4,})(/|$)", s):
        return "random_id"
    # ID code (letter + digits) or version code (PED001.3)
    if re.fullmatch(r"[A-Za-z]\d{5,8}", s) or re.fullmatch(r"[A-Za-z]{2,5}\d{2,4}(\.\d{1,3})?", s):
        return "random_id"

    # 7. Slug: readable content (dashed/underscored words or date+slug)
    toks = re.split(r"[-_/.\s]+", s)
    readable = [t for t in toks if t.isalpha() and len(t) >= 3]
    if len(readable) >= 2:
        return "slug"
    if re.search(r"/\d{4}/\d{2}/[a-z]", s):
        return "slug"

    return "slug"  # default fallback for unclassifiable readable tokens


def main() -> int:
    path = PROJECT_ROOT / "data/annotate/clean_test.csv"
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    for r in rows:
        r["label_a"] = label(r["path"])

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "path", "label_a", "label_b"])
        w.writeheader()
        w.writerows(rows)

    from collections import Counter
    dist = Counter(r["label_a"] for r in rows)
    print(f"Labeled {len(rows)} rows (label_a):")
    for c, n in dist.most_common():
        print(f"  {c:<12} {n:>4}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
