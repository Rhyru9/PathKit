#!/usr/bin/env python3
"""
label_annotate.py — Apply consistent labeling rules to data/annotate/sample.csv.

This is a first-pass auto-annotation to seed the manual review. Rules follow
data/annotate/guidelines.md. Output goes to data/annotate/sample_labeled.csv
so the original sample.csv (empty labels) stays intact for the manual pass.
"""

import csv
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
HEX32_RE = re.compile(r"^[0-9a-f]{32}$")
ID_CODE_RE = re.compile(r"^[A-Za-z]\d{5,8}$")
PURE_NUM_RE = re.compile(r"^\d{5,10}$")
NIP_NAME_RE = re.compile(r"^\d{12,16}-[A-Za-z]")  # NIP + name -> slug
VERSION_RE = re.compile(r"^[A-Za-z]{2,5}\d{2,4}(\.\d{1,3}){1,2}$")

ASSET_EXT = {".js", ".css", ".map", ".min.js", ".bundle.js"}
FILE_EXT = {
    ".xml", ".html", ".json", ".pdf", ".csv", ".txt", ".n3", ".nt",
    ".rdf", ".ris", ".bib", ".enw", ".refer", ".rss", ".rdf", ".doc", ".xls",
}

# Manual decisions for cases the rules can't confidently resolve.
# Keyed by the raw path token (as it appears in sample.csv).
MANUAL_OVERRIDES = {
    "slot88": "slug",                 # "slot" + number, spam slug
    "%233226": "random_id",            # "#3226" -> numeric fragment
    "14061-39bbd0a": "random_id",       # number + hex fragment
    "qc": "slug",                      # short abbreviation
    "setjen%3D5Fpdspk": "encoded",      # =5F org-code encoding
    "8253-2": "random_id",             # number-number (ID + page)
    "2278-2": "random_id",
    "256532-2": "random_id",
    "artikel4": "slug",                # "article 4"
    "77907-2c69d74": "random_id",       # number + hex
    "568-2": "random_id",
    "menambat%2Bhati": "slug",          # %2B = space -> "menambat hati"
}

def url_decode(raw: str) -> str:
    return re.sub(r"%([0-9A-Fa-f]{2})", lambda m: chr(int(m.group(1), 16)), raw)

def label(path: str) -> str:
    if path in MANUAL_OVERRIDES:
        return MANUAL_OVERRIDES[path]

    decoded = url_decode(path)
    s = decoded.lower()

    # 1. Noise / pure special chars
    if not s or re.fullmatch(r"[%{}\[\]<>#\\s]+", s) or len(s) < 2:
        return "noise"

    # 2. Encoded (base64/JWT or =XX hex chains)
    if re.search(r"eyJ[A-Za-z0-9+/=]{20,}", s):
        return "encoded"
    if re.search(r"(?:=[0-9A-Fa-f]{2}){2,}", s):
        return "encoded"

    # 3. Search (query with ? and =)
    if "?" in s and "=" in s:
        return "search"

    # 4. Random IDs (pure identifiers)
    if UUID_RE.match(s):
        return "random_id"
    if HEX32_RE.match(s):
        return "random_id"
    if ID_CODE_RE.match(s):  # P9996589, K5651679
        return "random_id"
    if PURE_NUM_RE.match(s):
        return "random_id"
    if VERSION_RE.match(s):  # PED001.3, PED000.21
        return "random_id"
    # NIP + readable name -> numeric slug
    if NIP_NAME_RE.match(s):
        return "slug"
    # random alphanumeric (mixed case + has digits + short + no separator)
    if (
        re.fullmatch(r"[A-Za-z0-9]{5,12}", s)
        and re.search(r"\d", s)
        and re.search(r"[A-Z]", path)
        and re.search(r"[a-z]", path)
    ):
        return "random_id"

    # 5. Asset (static web files)
    for ext in sorted(ASSET_EXT, key=len, reverse=True):
        if s.endswith(ext):
            return "asset"

    # 6. File (documents)
    for ext in FILE_EXT:
        if s.endswith(ext):
            return "file"

    # 7. Slug (readable content)
    # readable tokens (2+ alpha words) OR single readable word
    toks = re.split(r"[-_/.\s]+", s)
    toks = [t for t in toks if t]
    readable = [t for t in toks if t.isalpha() and len(t) >= 3]
    if len(readable) >= 2:
        return "slug"
    if len(readable) == 1:
        return "slug"
    # numeric slug: number-name
    if re.match(r"^\d{1,5}-[a-z]", s):
        return "slug"

    return "ambiguous"


def main() -> None:
    src = PROJECT_ROOT / "data/annotate/sample.csv"
    dst = PROJECT_ROOT / "data/annotate/sample_labeled.csv"

    rows = []
    with open(src, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    labeled = []
    for row in rows:
        lbl = label(row["path"])
        row["label"] = lbl
        labeled.append(row)

    with open(dst, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "path", "label"])
        for row in labeled:
            writer.writerow([row["id"], row["path"], row["label"]])

    from collections import Counter
    dist = Counter(r["label"] for r in labeled)
    print("Label distribution:")
    for c, n in dist.most_common():
        print(f"  {c:<14} {n:>5}")
    print(f"\nWrote {len(labeled)} rows -> {dst}")


if __name__ == "__main__":
    main()
