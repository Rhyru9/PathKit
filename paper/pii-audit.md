# PII & License Audit — Findings + Sanitization Protocol

> Blocker for publication and any public artifact release. This document
> records what was found, the legal/licensing posture, and the sanitization
> steps required before the dataset can be shared.

---

## 1. Audit Findings (script: `scripts/audit_pii.py`)

### `data/paths.txt` (22,583 rows)

| PII type | Count | Severity | Example |
|---|---|---|---|
| NIP + name (candidate) | 908 | 🔴 High | `[REDACTED_NIP_NAME]` |
| Staff ID code (`P/K`+digits) | 2,067 | 🔴 High | `[REDACTED_ID_CODE]` |
| Credential | 3 | 🔴 Critical | `[REDACTED_CREDENTIAL]` |
| Email | 5 | 🔴 High | (3 matches overlap credential rows) |
| Phone | 0 | — | — |

### `data/endpoints.txt` (447,266 rows)

| PII type | Count | Severity | Example |
|---|---|---|---|
| Encoded author name (`/creators/…=3A…`) | 9,520 | 🟠 Medium | `/cgi/exportview/creators/[REDACTED_NAME]` |
| NIP + name (candidate) | 3,157 | 🔴 High | `/profil/…1041727503…` |
| Staff ID code | 2,112 | 🔴 High | `/referensi…/[REDACTED_ID_CODE]` |
| Email | 6 | 🔴 High | (in `katalog` URLs) |
| Phone | 3 | 🔴 High | (in `sekolah.data…` URLs) |
| Credential | 3 | 🔴 Critical | `…/sys/login:[REDACTED_CREDENTIAL]` |

> **NIP-name caveat:** the NIP rule (`12–16 digits + dash + letter`) is a
> *candidate* detector. It catches genuine NIP+name pairs **and** some NIP-like
> prefixes followed by a title/FAQ heading (e.g. `…-[TITLE]`). The
> label is therefore "candidate", not confirmed PII. Formal NIP format
> validation (18-digit checksum) is a follow-up, not yet implemented.

> **Encoded-name scope:** only `=3A`/`=2E` within a `/creators/` route are
> treated as author names (9,520). `/subjects/` (topical terms, 308), and other
> `=3A` uses are intentionally NOT redacted.

### 🔴 Critical finding: credential-like strings

Six rows match the `login:<email>:<password>` format: three in each input
file. Email counts overlap these credential rows.

```
login:[REDACTED_EMAIL]:[REDACTED_SECRET]
login:[REDACTED_EMAIL]:[REDACTED_SECRET]
login:[REDACTED_EMAIL]:[REDACTED_SECRET]
```

These are **credential leaks** (likely school/teacher SSO accounts for
`sso.data.kemendikdasmen.go.id`), not merely PII. They must be redacted with
highest priority and reported as a security incident — they are not a benign
dataset artifact.

---

## 2. Legal & Licensing Assessment

| Aspect | Assessment | Confidence |
|---|---|---|
| **Source** | Indonesian government (Kemendikdasmen, Kemdikbud) — public body | observed |
| **Public info law** | UU No. 14/2008 (Keterbukaan Informasi Publik) — gov info is generally public | high |
| **Personal data law** | UU No. 27/2022 (PDP) — names + NIP are personal data; redistribution requires legal basis | high |
| **Crawl ToS** | Source terms of use / robots.txt not yet checked | **unknown** |
| **License to redistribute** | Not established — cannot claim a license on crawled data | **blocked** |

**Conclusion:** the *code, taxonomy, and aggregate statistics* can be released.
The *raw* and *sanitized* path data **cannot** be claimed publishable until (a)
the source ToS is verified and (b) a legal basis under PDP is established.

---

## 3. Sanitization Protocol

Three tiers:

| Tier | Action | Output |
|---|---|---|
| **T0 — aggregate only** | publish counts, distributions, taxonomy (no raw paths) | always safe |
| **T1 — sanitized sample** | redact/remove NIP+name, ID codes, emails, phones, credentials; keep structural variety | *development copy only* — not yet cleared for publication |
| **T2 — raw release** | only after legal review + source ToS confirmed | blocked |

### Redaction rules (T1)

1. **Credential** (`login:email:password`) → drop entire token.
2. **Email** (standalone or embedded) → redact to `[EMAIL]`, preserve structure.
3. **NIP + name** (`^\d{12,16}-[A-Za-z]`, candidate) → redact segment to `[NIP_NAME]`.
4. **ID code** (`^[A-Za-z]\d{5,8}$`, segment-aware) → redact to `[ID_CODE]`.
5. **Phone** (`+62…`, `08…`) → redact to `[PHONE]`.
6. **Encoded author name** (`/creators/…=3A…=2E…` only) → redact name to `[NAME]`.

> **Normalization caveat:** the sanitizer percent-decodes (UTF-8) before
> redacting, so `data/sanitized/*` is a **normalized** representation, not a
> byte-for-byte copy of the raw data.

### Deliverable

`scripts/sanitize_dataset.py`:
- reads `paths.txt` / `endpoints.txt`,
- applies the redaction rules (shared `scripts/pii_rules.py`),
- writes `data/sanitized/paths_clean.txt` + `endpoints_clean.txt`,
- **re-audits** the output and fails (exit 1) if any credential/email/phone/
  id_code/nip_name survives,
- emits `data/sanitized/redaction_report.json`.

---

## 4. Open Items (before release)

- [ ] Confirm source `robots.txt` / terms of use (crawl legitimacy).
- [ ] Establish a legal basis for publishing the sanitized sample (PDP art. 4).
- [ ] Decide: publish T0 (aggregate) only, or T1 (sanitized sample)?
- [ ] Re-scan for secrets (tokens/keys) beyond the credential strings found.
- [ ] Formal NIP checksum validation (reduce NIP+name false positives).
- [ ] Report the credential leak via responsible disclosure (BSSN/Kemendikdasmen).

---

## 5. Status

| Item | Status |
|---|---|
| PII audit script | ✅ `scripts/audit_pii.py` + `data/audit/pii_report.json` |
| Findings documented | ✅ this file |
| Sanitization script | ✅ `scripts/sanitize_dataset.py` (re-audit passes) |
| Sanitized copy | ✅ `data/sanitized/*` — development copy; **not cleared for publication** |
| License verified | ❌ blocked (unknown ToS) |
| Clean, independently-annotated test set | ❌ pending |
