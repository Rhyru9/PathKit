# Slug Detection Research

> Developer sees slug as a URL segment. Analyst sees slug as **natural-language content addressing → the only semantic identifier type.**

---

## 1. What Makes a Slug

A slug is the **only human-readable, semantic** URL path token. Unlike all other identifiers:

| Slug | UUID | Timestamp | Hash | Base64 |
|---|---|---|---|---|
| Natural language | Structured hex+dash | Numeric/time | Pure hex | Encoded data |
| Readable words | Machine identity | Event time | Content hash | Encrypted payload |
| Semantic | Zero semantics | Temporal only | Content-addressed | Opaque |
| `panduan-belajar-online` | `550e8400-e29b-...` | `1718201234` | `9e107d9d...` | `eyJpdiI6...` |

---

## 2. Slug Signals (Feature Engineering)

### A. Structural

- **Dashes** (`-`) — primary slug delimiter (strong positive)
- **Underscores** (`_`) — secondary delimiter (weaker positive)
- **No dots, no slashes** — slugs are single segments

### B. Linguistic

- **Readable tokens** — 3+ consecutive alpha chars in tokens
- **Vowel ratio** — natural language has ~40% vowels; gibberish/hashes have <20%
- **Common word hits** — stopwords like `dan`, `di`, `cara`, `the`, `how`
- **Gibberish check** — 4+ consecutive consonants → not a slug

### C. Entropy

- **Low per-token entropy** — natural words have entropy ~3-4 bits
- **High per-token entropy** — hashes/IDs have entropy ~6-8 bits

### D. Anti-Signals (push away from slug)

- **Anti-slug tokens**: `wp-content`, `assets`, `static`, `node_modules`, `vendor`
- **UUID embedded in text**: CMS hybrid leak
- **=XX hex encoding**: internal routing code
- **Pure digits**: employee ID, document number

---

## 3. Feature Vector (23 dimensions)

| Feature | Range | Signal |
|---|---|---|
| `len_norm` | 0–1 | Length normalization |
| `has_dash` | 0/1 | Dash present |
| `has_underscore` | 0/1 | Underscore present |
| `has_dot` | 0/1 | Dot present (file extension) |
| `has_slash` | 0/1 | Slash present (multi-segment) |
| `dash_ratio` | 0–1 | Dash density |
| `digit_ratio` | 0–1 | Digit density |
| `entropy_norm` | 0–1 | Shannon entropy |
| `vowel_ratio` | 0–1 | Linguistic naturalness |
| `has_gibberish` | 0/1 | 4+ consonant run |
| `token_count_norm` | 0–1 | Number of tokens |
| `avg_token_len_norm` | 0–1 | Average token length |
| `readable_count_norm` | 0–1 | Readable tokens (3+ alpha) |
| `common_word_hits` | 0–1 | Stopword matches |
| `anti_slug_hits` | 0–1 | System/asset path tokens |
| `token_entropy_norm` | 0–1 | Avg per-token entropy |
| `is_hex` | 0/1 | Pure hex string |
| `is_uuid` | 0/1 | UUID pattern match |
| `is_file_ext` | 0/1 | Known file extension |
| `is_catalog` | 0/1 | Encoded catalog pattern (=3A, =2E) |
| `has_special` | 0/1 | Special characters |
| `is_noise` | 0/1 | Short + special = noise |
| `first_is_num` | 0/1 | First token is numeric |

---

## 4. Auto-Labeling Heuristics

Used for self-supervised training (no manual labels needed):

```
1. UUID patterns          → random_id
2. Encoded signals (=3A)  → encoded
3. Asset patterns (.js)   → asset
4. File extensions        → file
5. /api/, /rest/          → api
6. ? and =                → search
7. 2+ readable tokens OR
   common word hits       → slug
8. Undetermined           → negative example
```

**Tightened rules:** No loose defaults — must have clear signal.

---

## 5. Post-Filters (after classification)

Even if the classifier says "slug", these reject it:

| Filter | Reason |
|---|---|
| No `-` or `_` in path | Single words aren't real slugs |
| Starts or ends with `-` | Truncated slug |
| Contains `__trashed` | WordPress trash artifact |
| Contains embedded UUID | CMS hybrid (slug+UUID concatenation) |
| Uncertainty gate | Low confidence → send to review |

---

## 6. Classifier Architecture

```
URLIntentModel (logistic classifier, 7 classes)

Training:
    stochastic gradient descent, lr=0.03
    80/20 train split
    per-sample weighting

Prediction:
    weighted feature sum → sigmoid → probability per class
    top-1 = classification
    margin = top1_score - top2_score
    uncertain if: confidence < 0.55 OR margin < 0.08

Classes:
    slug, api, asset, search, random_id, file, encoded
```

---

## 7. Classification Pipeline

```
paths.txt
    ↓
load_paths()          → 230,200 raw tokens
    ↓
auto_label()          → 222,812 labeled (heuristic)
    ↓
train(model)          → 178,249 training examples
    ↓
predict(all)          → 230,200 classified
    ↓
post-filter           → remove noise patterns
    ↓
export                → slugs.txt + slugs_review.txt
```

---

## 8. Integration with Identifier Detectors

```
For each path:
    1. uuid.score > 0.5      → random_id   (skip slug classifier)
    2. timestamp.score > 0.5 → api/search
    3. hash.score > 0.5      → asset/api
    4. base64.score > 0.5    → api
    5. other.score > 0.5     → file
    6. Else                  → slug classifier (ML)
```

Identifier detectors filter out ~30% of paths before the ML classifier runs, dramatically reducing false slug positives.

---

## 9. Dataset Results (230,200 paths)

| Class | Count | % |
|---|---|---|
| file | 133,346 | 57.9% |
| random_id | 63,585 | 27.6% |
| slug | 23,847 | 10.4% |
| encoded | 9,405 | 4.1% |
| search | 10 | 0.0% |
| asset | 7 | 0.0% |
| api | 0 | 0.0% |

**Slugs exported:** 15,897 (post-filtered from 23,847 predictions)

---

## 10. Key Insight

**Slug is the DEFAULT — everything else is a rejection.**

The slug classifier's job is not to find slugs — it's to confirm that the path survived every other detector. If uuid/timestamp/hash/base64/other all return 0.0 AND the text looks like natural language → it's a slug.
