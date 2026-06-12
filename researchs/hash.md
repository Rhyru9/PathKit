# Hash Detection Research

> Developer sees hash as a crypto output. Analyst sees hash as **content-addressed pointer → non-semantic system artifact.**

---

## 1. Common Hash Types in URLs

| Hash | Hex chars | Common context |
|---|---|---|
| MD5 | 32 | Legacy CDN, file integrity |
| SHA1 | 40 | Git, API tokens, Medium |
| SHA256 | 64 | Modern CDN, Webpack, S3 |
| Truncated | 8–16 | Bundler chunks, cache busters |

---

## 2. Developer Bias → Analyst Correction

| Developer assumption | Analyst correction |
|---|---|
| Hash = file integrity → ignore | Hash = **content-addressed storage** |
| "Just random hex" → neutral | "Pure hex entropy = strongest non-semantic signal" |

---

## 3. Context → Classification

| Context | Classification | Confidence |
|---|---|---|
| Hash **alone** | API / storage object | HIGH |
| Hash **\+ file extension** | Bundler artifact / CDN | HIGH |
| Hash **\+ path prefix** | Object storage / CMS backend | HIGH |
| Hash **\+ slug words** | Broken CMS design | LOW (review) |

---

## 4. Hash vs UUID vs Timestamp

| Type | Structure | Meaning |
|---|---|---|
| UUID | structured hex+dash | object **identity** |
| Timestamp | numeric/time | event **time** |
| Hash | pure hex entropy | content **identity** (highest entropy, lowest semantics) |

---

## 5. Detection Patterns

```
MD5:    \b[a-f0-9]{32}\b
SHA1:   \b[a-f0-9]{40}\b
SHA256: \b[a-f0-9]{64}\b
Generic: \b[a-f0-9]{24,128}\b
```

---

## 6. Scoring Model

```python
def hash_score(s):
    s = s.lower()
    score = 0.0

    # MD5
    if re.search(r"\b[a-f0-9]{32}\b", s):    score += 0.8
    # SHA1
    if re.search(r"\b[a-f0-9]{40}\b", s):    score += 0.85
    # SHA256
    if re.search(r"\b[a-f0-9]{64}\b", s):    score += 0.9
    # Generic long hex
    if re.search(r"\b[a-f0-9]{24,}\b", s):   score += 0.6

    # Entropy bonus
    entropy = len(set(s)) / max(len(s), 1)
    if entropy > 0.7:                         score += 0.2

    return min(score, 1.0)
```

---

## 7. Analyst Decision Rules

- **Hash alone** → NOT slug → API / storage
- **Hash + .js/.css/.map** → bundler artifact → `asset`
- **Hash + readable text** → CMS hybrid leak → `review`

---

## 8. Systems that use hashes in URLs

CDN (Cloudflare, Akamai) · Webpack/Vite bundlers · S3/object storage · Git-like systems · Media pipelines · Caching layers

---

## 9. Implementation Notes

- Hash has the **lowest semantic value** of all identifier types
- High entropy + restricted alphabet = strong hash signal
- Bundler chunks: `name-<hash>.js` pattern is extremely common
- Truncated hashes (8-16 chars) are ambiguous → score lower
