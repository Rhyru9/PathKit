# "Other" Category Research — Internal Routing & System Artifacts

> These are NOT identifiers (UUID/timestamp/hash/base64) and NOT slugs.
> They are **internal routing codes, versioned references, and organizational unit identifiers.**

---

## 1. What "Other" Captures

Patterns that don't fit any identifier type but are clearly non-semantic system artifacts:

| Pattern | Example | Meaning |
|---|---|---|
| **Org unit codes** | `ditjen=5Fbudaya=5Fsesditjen=5Fupt26` | Government bureaucracy routing |
| **Dotted version paths** | `PED003.3.4` | Versioned document/module reference |
| **Concatenated IDs** | `pskp.kemdikbud2.941.761.133...` | Analytics/counter internal path |
| **Short pure numbers** | `70032380` | Employee NIP, document ID |
| **Encoded delimiters** | `=5F` → `_`, `=3D` → `=` | Inline hex encoding in path |

---

## 2. Why They're Not Slugs

| Slug | "Other" |
|---|---|
| `artikel/panduan-belajar-online` | `ditjen=5Fbudaya=5Fsesditjen=5Fupt26` |
| Human-readable content | Machine-readable routing |
| Natural language tokens | Organizational codes |
| Stable entity page | Internal navigation artifact |
| Separated by `-` | Separated by `=5F` (encoded `_`) |

---

## 3. Detection Patterns

### A. Encoded Delimiter Paths (`=XX` in-path encoding)

```
ditjen=5Fbudaya=5Fsesditjen=5Fupt26
badan=5Fbahasa=5Fsesban=5Fupt30
```

- `=5F` = `_` (underscore)
- `=3D` = `=` (equals)
- Structure: `unit=5Fsubunit=5Fsubsubunit`
- **Signal**: multiple `=XX` hex encodings in sequence = internal routing code

### B. Dotted Version Paths

```
PED003.3.4
PED003.3.7
PED3.3.18
```

- `PED` = module prefix
- `003.3.4` = version/section numbering
- **Signal**: alpha prefix + dotted numeric hierarchy

### C. Short Numeric IDs

```
70032380
20325266
```

- 5–10 digit pure numbers
- **Signal**: not a year (too short/long), not unix timestamp (out of range), just an ID

---

## 4. Scoring Model

```python
def other_score(s):
    score = 0.0

    # Encoded delimiters (=5F, =3D, =2E)
    encoded_delims = len(re.findall(r"=[0-9A-Fa-f]{2}", s))
    if encoded_delims >= 3:
        score += 0.8

    # Dotted version pattern (PREFIX###.###.###)
    if re.search(r"\b[A-Z]{2,5}\d{2,4}\.\d{1,3}\.\d{1,3}", s):
        score += 0.7

    # Short pure numeric ID (5-10 digits, not a timestamp)
    if re.fullmatch(r"\d{5,10}", s):
        score += 0.5

    return min(score, 1.0)
```

---

## 5. Dataset Findings (230,200 paths)

| "Other" sub-type | Count |
|---|---|
| Encoded delimiter paths (`=5F` chains) | ~389 |
| Dotted version paths (`PED003.3.4`) | ~245 |
| Short numeric IDs (5-10 digits) | ~88,720 |
| Special char noise | 0 |
| **Total "other" (non-slug, non-identifier)** | **~89,354 (38.8%)** |

---

## 6. Integration

"Other" is the **catch-all rejection filter** — applied AFTER uuid/timestamp/hash/base64:

```
if uuid_score > 0.5    → random_id
elif timestamp > 0.5   → api/search
elif hash_score > 0.5  → asset/api
elif base64 > 0.5      → api
elif other_score > 0.5 → file/other  ← catch-all non-slug
elif slug_signals      → slug
else                   → file (default)
```

---

## 7. Key Insight

**"Other" is not a classification — it's a rejection: "this is definitely not a slug."**

It captures the 38.8% of paths that are neither content (slug) nor identifiable (uuid/timestamp/hash/base64). These are the internal plumbing of web applications — routing codes, document version numbers, employee IDs.
