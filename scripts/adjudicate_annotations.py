#!/usr/bin/env python3
"""Resolve annotator disagreements into a separate final label column.

This is an expert-assisted adjudication pass. It never overwrites label_a or
label_b and must not be reported as a third independent annotator.
"""

import argparse
import csv
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import unquote

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VALID = {"slug", "api", "asset", "search", "random_id", "file", "encoded"}
UUID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)
HASH_RE = re.compile(r"\b[0-9a-f]{32,64}\b", re.IGNORECASE)
ID_RE = re.compile(r"(?<![A-Za-z])[A-Za-z]\d{5,8}(?!\w)")
API_RE = re.compile(r"/(?:api|rest|graphql|cgi|export|data)(?:/|$)", re.IGNORECASE)
ASSET_EXT_RE = re.compile(r"\.(?:js|css|map|png|jpg|jpeg|gif|svg|woff2?)(?:$|[?#])", re.I)
FILE_EXT_RE = re.compile(
    r"\.(?:pdf|xml|html?|txt|csv|json|n3|nt|rdf|ris|bib|enw|refer|docx?|xlsx?|zip)"
    r"(?:$|[?#])",
    re.I,
)


def adjudicate(path: str, label_a: str, label_b: str) -> str:
    if label_a == label_b:
        return label_a
    decoded = unquote(path, encoding="utf-8", errors="replace")
    lower = decoded.lower()
    if "%" in path or re.search(r"=[0-9a-f]{2}", path, re.I):
        if label_a == "encoded" or label_b == "encoded":
            return "encoded"
    # Programmatic route context outranks query/file/identifier ambiguity.
    if API_RE.search(lower):
        return "api"
    if "?" in decoded and "=" in decoded:
        return "search"
    if ASSET_EXT_RE.search(lower):
        return "asset"
    if FILE_EXT_RE.search(lower):
        return "file"
    if UUID_RE.search(lower) or HASH_RE.search(lower) or ID_RE.search(decoded):
        return "random_id"
    # A readable multi-token route is content, not an opaque identifier.
    words = [w for w in re.split(r"[-_/.\s]+", lower) if w.isalpha() and len(w) >= 3]
    if len(words) >= 2:
        return "slug"
    return "random_id" if "random_id" in (label_a, label_b) else "slug"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/annotate/clean_test.csv")
    args = parser.parse_args()
    path = PROJECT_ROOT / args.input
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    required = {"id", "path", "label_a", "label_b"}
    if not rows or not required <= set(rows[0]):
        raise SystemExit("Expected id,path,label_a,label_b columns")
    for row in rows:
        if row["label_a"] not in VALID or row["label_b"] not in VALID:
            raise SystemExit(f"Invalid labels at row {row['id']}")
        row["label_final"] = adjudicate(row["path"], row["label_a"], row["label_b"])
    fd, temporary = tempfile.mkstemp(prefix="clean_test.", suffix=".csv", dir=path.parent)
    os.close(fd)
    with open(temporary, "w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=["id", "path", "label_a", "label_b", "label_final"]
        )
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)
    disagreements = sum(row["label_a"] != row["label_b"] for row in rows)
    print(f"Rows adjudicated: {len(rows)}")
    print(f"Disagreements retained: {disagreements}")
    print("Added label_final without overwriting either annotator column.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
