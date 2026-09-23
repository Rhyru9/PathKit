# Dataset Provenance Checklist

> Must be completed before the manuscript or any public artifact release.
> Fields marked `[UNKNOWN]` block publication until filled in.

---

## 1. Crawl Provenance

| Field | Value | Status |
|---|---|---|
| **Seed URL(s)** | `[UNKNOWN]` — e.g. `https://kemdikdasmen.go.id`, `https://referensi.data.kemendikdasmen.go.id` | ❌ |
| **Crawl depth** | `[UNKNOWN]` | ❌ |
| **Tool name + version** | DIFIND / ReconArchitectAgent — exact version `[UNKNOWN]` | ❌ |
| **Collection date** | 2026-06-12 (file mtime) — confirm | ⚠️ |
| **Crawl mode** | offline extraction (no-fetch) | ✅ |
| **Deduplication** | both files 0 duplicates | ✅ |
| **Normalization** | strip whitespace; original case preserved; no domain stripping | ✅ |

## 2. Legal & Licensing

| Field | Value | Status |
|---|---|---|
| **robots.txt / ToS** | `[UNKNOWN]` — check `kemdikdasmen.go.id/robots.txt` | ❌ |
| **Public info basis** | UU No. 14/2008 (Keterbukaan Informasi Publik) | ⚠️ |
| **Personal data basis** | UU No. 27/2022 (PDP) — names + NIP present | ❌ |
| **Redistribution license** | `[UNKNOWN]` — cannot claim | ❌ |

## 3. PII & Security

| Field | Value | Status |
|---|---|---|
| **PII audit** | ✅ 6 credentials, 4,065 NIP/ID, 9,520 author names found | ✅ |
| **Sanitization** | ✅ re-audit passes (no sensitive PII survives) | ✅ |
| **Credential leak reported** | ❌ not yet (responsible disclosure to BSSN/Kemendikdasmen) | ❌ |

## 4. Test Set Protocol

| Field | Value | Status |
|---|---|---|
| **Clean test set** | `data/annotate/clean_test.csv` (600, seed=2026) | ⚠️ unlabeled |
| **Annotator 1** | ❌ pending | ❌ |
| **Annotator 2** | ❌ pending | ❌ |
| **Cohen's κ** | ❌ pending (`scripts/agreement.py`) | ❌ |
| **Disagreement adjudication** | ❌ pending | ❌ |
| **Test freeze** | ❌ pending | ❌ |

## 5. Publication Decision

- [ ] Publish **T0** (aggregate stats + taxonomy + code) — safe now.
- [ ] Publish **T1** (sanitized sample) — after ToS + legal basis.
- [ ] Publish **T2** (raw) — likely never (PII).

---

**Blockers:** seed URL, crawl depth, tool version, robots.txt/ToS, legal basis,
2nd annotator + κ, credential-leak report.
