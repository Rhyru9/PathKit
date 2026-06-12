# Base64 Detection Research

> Developer sees Base64 as encoding. Analyst sees Base64 as **encrypted/encoded data transport → strong API/auth signal → never a slug.**

---

## 1. Hash vs Base64 — Different Identifier Classes

| | Hash | Base64 |
|---|---|---|
| **Alphabet** | Pure hex `[a-f0-9]` | Full `[A-Za-z0-9+/=]` or URL-safe `[A-Za-z0-9-_]` |
| **Length** | Fixed (32/40/64) | Variable (40–200+) |
| **Meaning** | Content addressing | Data transport (encoding) |
| **URL context** | CDN / storage / bundler | Session / auth / encrypted params |
| **Entropy** | High (16 chars) | Very high (64 chars) |
| **Semantic value** | Zero | Zero (even less — encrypted) |

---

## 2. Common Base64 Patterns in URLs

### A. JWT / Laravel Encrypted Tokens

```
eyJpdiI6Ii9CVlVOWkcyeWFxVWY2d3BqSVh6dHc9PSIsInZhbHVlIjoiVkZFSzAxVU1u...
```

- Prefix `eyJ` = Base64 of `{"` (JSON start)
- 80–200+ chars, mixed case, `+` `/` `=` present
- **Meaning**: Laravel session cookie, CSRF token, encrypted payload

### B. Base64 Query Parameters

```
?token=YWJjZGVmZ2hpamtsbW5vcA==
?state=dXNlcl9pZD0xMjM0JnJlZGlyZWN0PS9ob21l
```

### C. URL-safe Base64 (no padding)

```
dXNlcl9pZD0xMjM0JnJlZGlyZWN0PS9ob21l
```

- Often used as short-lived tokens in redirects, OAuth flows

---

## 3. Scoring Model

```python
def base64_score(s):
    score = 0.0

    # JWT/Laravel prefix
    if s.startswith("eyJ"):
        score += 0.9

    # Classic Base64: mixed case, +/=, 40+ chars
    if re.search(r"[A-Za-z0-9+/=]{40,}", s):
        has_upper = bool(re.search(r"[A-Z]", s))
        has_lower = bool(re.search(r"[a-z]", s))
        if has_upper and has_lower:
            score += 0.7

    # High entropy + large alphabet (not just hex)
    chars = set(s)
    if len(chars) > 30 and len(s) > 40:
        score += 0.3

    return min(score, 1.0)
```

---

## 4. Decision Rules

- **Base64 token in path** → NEVER slug → `api` or `encoded`
- **Base64 in query param** → `search` (authenticated API call)
- **Base64 + cookie prefix** → `api` (session/auth endpoint)

---

## 5. Dataset Findings (230,200 paths)

| Pattern | Count |
|---|---|
| JWT/Laravel tokens (`eyJ...`) | 927 |
| Classic Base64 (mixed case, 40+) | ~2,900 total, ~900 clean |

Key insight: **Base64 = encrypted data. If you can't read it, neither can the URL classifier treat it as a slug.**
