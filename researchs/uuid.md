# UUID Detection Research

> Developer sees UUID as a format. Analyst sees UUID as a **high-confidence non-semantic identifier signal**.

---

## 1. UUID Pattern (RFC 4122)

```
550e8400-e29b-41d4-a716-446655440000
```

| Attribute | Value |
|---|---|
| Structure | 8-4-4-4-12 |
| Total chars | 36 (including dashes) |
| Alphabet | hex only (`[0-9a-fA-F]`) |
| Version nibble | `[1-5]` at position 13 |
| Variant nibble | `[89abAB]` at position 17 |

### Standard Regex

```
^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$
```

---

## 2. Developer Bias → Analyst Correction

| Developer assumption | Analyst correction |
|---|---|
| UUID = database ID → ignore semantics | UUID = **strong non-content signal** |
| UUID = safe identifier → treat as neutral | UUID in path = **high-confidence class hint** |
| UUID = stable routing key → ignore as noise | UUID = **needs context to classify** |

---

## 3. Context → Classification Mapping

| UUID context | Classification | Confidence |
|---|---|---|
| UUID **alone** in path | API / object endpoint | HIGH |
| UUID **mixed with words** | Bad CMS design (hybrid slug) | LOW (review) |
| UUID **\+ file extension** | CDN / object storage (asset) | HIGH |
| UUID **\+ query param** | Database fetch (API) | HIGH |

---

## 4. Analyst Signals (beyond regex)

| Signal | What to detect |
|---|---|
| **Entropy spike** | Uniform hex distribution → high entropy |
| **Character constraint** | Only `[0-9a-f]` — restricted alphabet |
| **Structural hyphens** | Hyphens are structural, NOT linguistic |
| **Semantic isolation** | UUID tokens are never real words |

---

## 5. Scoring Model (preferred over boolean)

```python
def uuid_score(s: str) -> float:
    score = 0.0

    # Partial match: long hex-dash string
    if re.search(r"[0-9a-fA-F\-]{32,}", s):
        score += 0.4

    # Full strict UUID match
    if re.fullmatch(r"(?:[0-9a-fA-F]{8}-){4}[0-9a-fA-F]{12}", s):
        score += 0.9

    # Non-UUID characters present → penalize
    if re.search(r"[g-zG-Z]", s):
        score -= 0.5

    # Exactly 4 dashes = UUID structure
    if s.count("-") == 4:
        score += 0.2

    return min(max(score, 0.0), 1.0)
```

### Why scoring beats boolean

- Boolean `is_uuid` forces binary decision with no nuance
- Scoring captures partial, embedded, and malformed UUIDs
- Scoring feeds naturally into classifier feature vectors
- Penalization prevents false positives on lookalike strings

---

## 6. Implementation in PathKit

### New feature: `uuid_score` (0.0–1.0)

Replaces the binary `is_uuid` flag with a continuous score:

- 0.0 = definitely not UUID-like
- 0.4–0.6 = UUID-like substring (embedded, partial)
- 0.9–1.0 = strict UUID match

### New feature: `uuid_embedded` (0.0 or 1.0)

Detects UUIDs embedded inside larger strings (CMS hybrid pattern):

```
/article/550e8400-e29b-41d4-a716-446655440000-learning-path
```

This is a **negative** signal for slug classification — pushes toward `random_id` or `review`.

### Classification rules (labeling.py)

```python
# Standalone UUID → random_id
if re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", s):
    return "random_id"

# UUID embedded in readable text → NOT slug (review/uncertain)
if UUID_REGEX.search(s) and len(readable) > 0:
    return None  # let classifier decide with uuid_score signal
```
