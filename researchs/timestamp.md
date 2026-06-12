# Timestamp Detection Research

> Developer sees timestamp as a format. Analyst sees timestamp as a **temporal access pattern — a state indicator of system design.**

---

## 1. Common Timestamp Formats

| Format | Example | Context |
|---|---|---|
| Unix seconds | `1718201234` | Log/API/event |
| Unix milliseconds | `1718201234123` | Real-time system, analytics |
| ISO date | `2026-06-12` | Export, blog, archive |
| ISO datetime | `2026-06-12T10:20:30Z` | Audit log, snapshot |
| Date path | `/2026/06/12/` | CMS blog archive |
| URL-encoded | `2026-06-12_10-20-30` | File naming |

---

## 2. Developer Bias → Analyst Correction

| Developer assumption | Analyst correction |
|---|---|
| Timestamp = time identifier → ignore | Timestamp = **temporal access pattern** |
| Timestamp = pagination cursor → neutral | Timestamp = **dynamic, time-scoped, non-canonical** |
| "Just another number" → skip | "When I see a timestamp, the URL is usually NOT a slug" |

---

## 3. Context → Classification Mapping

| Pattern | Classification | Confidence |
|---|---|---|
| Unix timestamp **alone** | API / system endpoint | HIGH |
| ISO date string **alone** | Export / log | HIGH |
| Date path **\+ slug words** (`/2026/06/12/article-title`) | **CMS hybrid** — slug but time-scoped | MEDIUM |
| Date path **alone** (`/2026/06/12/`) | Blog archive listing | MEDIUM |
| Timestamp **\+ query params** | Filtered search | HIGH |

---

## 4. Slug vs Timestamp (CRITICAL)

| Slug | Timestamp |
|---|---|
| semantic content | temporal index |
| stable | volatile |
| human readable | machine generated |
| entity page | state snapshot |

---

## 5. Types of Timestamp Signals

### A. Unix Timestamp (seconds)

```
/log/1718201234
```

Detection: `\b(1[6-9]\d{8}|2\d{9})\b`

Meaning: log endpoint, monitoring system, event stream. **NOT slug.**

### B. Millisecond Timestamp

```
/event/1718201234123
```

Detection: `\b1\d{12}\b`

Meaning: real-time system, analytics event, Kafka-like pipeline ID.

### C. Date Path (very common in CMS)

```
/2026/06/12/article-title
```

**This is IMPORTANT** — it's NOT a non-slug. It's a **hybrid: temporal + slug.** The classifier must distinguish:
- `/2026/06/12/` → archive listing (not slug)
- `/2026/06/12/article-title` → time-scoped slug (still slug)

### D. ISO Date String

```
2026-06-12T10:20:30Z
```

Meaning: export API, audit log, system snapshot.

---

## 6. Scoring Model

```python
def timestamp_score(s):
    score = 0.0

    # unix seconds (range: 1,600,000,000 – 2,999,999,999)
    if re.search(r"\b(1[6-9]\d{8}|2\d{9})\b", s):
        score += 0.7

    # unix milliseconds
    if re.search(r"\b1\d{12}\b", s):
        score += 0.8

    # ISO date YYYY-MM-DD
    if re.search(r"\d{4}-\d{2}-\d{2}", s):
        score += 0.5

    # Date path structure /YYYY/MM/DD/
    if re.search(r"/\d{4}/\d{2}/\d{2}/", s):
        score += 0.6

    return min(score, 1.0)
```

---

## 7. Key Analyst Decision Rules

### Rule 1: High timestamp → NOT slug

```
if timestamp_score(url) > 0.7:
    bias["slug"] -= 0.4
    bias["search"] += 0.3
```

### Rule 2: Timestamp + words = CMS hybrid slug

```
/2026/06/12/menteri-pendidikan
```

Classification: **slug** (but time-scoped content). The date path alone doesn't disqualify it — check if readable tokens follow.

### Rule 3: Timestamp alone = system endpoint

```
/log/1718201234
```

Classification: API / system / telemetry. **Never slug.**

---

## 8. Big Analyst Insight

Timestamp is NOT a "pattern" — it's a **state indicator of system design.**

| Before | After |
|---|---|
| `/log/1718201234` → slug ❌ | `/log/1718201234` → api: 0.85, slug: 0.10 |
| `/2026/06/12/article` → ? ❌ | slug: 0.75 (hybrid, still slug) |

---

## 9. Implementation Notes

- Timestamp detection MUST run AFTER percent-decoding
- Unix timestamp range is dynamic: `1600000000` (2020-09-13) to `2999999999` (2065-01-24)
- Date paths (`/YYYY/MM/DD/`) are NOT disqualifiers by themselves — context matters
- The scoring model is additive: multiple signals stack, capped at 1.0
