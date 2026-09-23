# Related Work — Comparison Matrix

> Goal: determine whether PathKit's contribution is (a) a new model, or
> (b) an empirically validated hybrid taxonomy + decision pipeline.
>
> ⚠️ Specific paper citations below need verification against primary sources
> before the manuscript. Tool references are well-known and stable.

---

## 1. URL / Path Classification

| System / Line of work | Task | Method | Granularity | Relevance to PathKit |
|---|---|---|---|---|
| URLNet (2018) | malicious URL detection | CNN over char/word embeddings | binary (benign/malicious) | same input (URL), different task (no *intent* taxonomy) |
| URLTran / transformer URL models | phishing + categorization | Transformers | binary or topical | supervised, no identifier decomposition |
| PhishTank / phishing classifiers | phishing detection | features + ML | binary | not about path token intent |
| Generic web-page topical classification | page topic from URL | lexical features + ML | topical (news/sports/…) | semantic, but not *opaque-vs-content* |

**Gap:** URL classification is dominated by *malicious/phishing* or *topical*
tasks. In the sources surveyed, we did not identify work that defines a
**seven-class intent taxonomy** (slug/api/asset/search/random_id/file/encoded)
aimed at reconnaissance triage. A broader systematic review remains necessary.

---

## 2. Semantic URL Analysis

| System | Task | Method | Note |
|---|---|---|---|
| URL segmentation / tokenization | split path into words | heuristics, dictionaries | component of SEO/analysis tools |
| Slug extraction (CMS plugins) | derive slug from URL | regex per-CMS | WordPress/Joomla specific |
| Semantic Web (RDF/OWL/linked data) | machine-readable meaning | ontologies | different notion of "semantic" (not path intent) |

**Gap:** "Semantic URL analysis" in the literature means *word segmentation* or
*ontology*. PathKit's notion — *does this token carry human-readable content
vs opaque system identity* — is distinct and under-explored.

---

## 3. Web Crawling & Endpoint Discovery

| Tool | Task | Method | Relevance |
|---|---|---|---|
| OWASP Amass / Subfinder | subdomain enum | passive/active DNS | discovery, not classification |
| dirb / gobuster / ffuf / dirsearch | path brute-force | wordlist + status codes | **rule-based**, no intent model |
| Burp Suite / Param Miner | parameter discovery | heuristics | parameter-level, not path-level |
| Nuclei | template scanning | YAML templates | vulnerability-specific |
| ReconArchitectAgent (DIFIND) | path/endpoint extraction | offline extraction | **the generator of this dataset** — no classification |

**Gap:** Endpoint discovery tools *enumerate* paths but do not *classify* them.
The analyst must manually triage thousands of results. PathKit targets exactly
this triage step.

---

## 4. Identifier / Token Classification

| Tool | Task | Method | Relevance |
|---|---|---|---|
| hashid / hash-identifier | identify hash type | regex per algorithm | single-signal, no context |
| TruffleHog / gitleaks | secret detection | regex + entropy | secrets, not path intent |
| JWT / base64 decoders | decode tokens | single-format | format-specific, no pipeline |
| UUID validators | detect UUID | regex | trivial, standalone |

**Gap:** Identifier detection exists as *isolated regex tools*. PathKit
**integrates** UUID/timestamp/hash/base64/routing-code detection into a single
ordered pipeline that feeds a classifier.

---

## 5. Security Reconnaissance

| System | Task | Method | Relevance |
|---|---|---|---|
| Attack-surface mapping (ASM) | inventory assets | crawlers + rules | enumeration, not intent |
| OWASP Amass / Recon-ng | recon automation | modular scripts | orchestration, no classification |
| Analyst triage workflows | prioritize findings | manual | **the human step PathKit automates** |

**Gap:** Recon tools produce *unclassified* endpoint lists. The analyst's
triage (which paths are content vs system artifacts) is manual and
unmeasured. PathKit provides a measurable, reproducible proxy for this step.

---

## 6. Hybrid Rule-Based + ML Systems

| System | Task | Method | Relevance |
|---|---|---|---|
| Spam filters (SpamAssassin + ML) | spam detection | rules + Bayes/ML | same *hybrid* pattern |
| IDS/IPS (Snort + ML) | intrusion detection | signatures + ML | rule-first, ML-second |
| Neuro-symbolic systems | reasoning | logic + neural | different domain, same idea |
| Cascade / pre-filter + ML | cost reduction | cheap rules filter, ML refines | **closest architectural analog** |

**Gap:** The *hybrid pattern* is established, but its application to **URL path
intent with layered decoding** as a pre-filter was not identified in the
sources surveyed. This combination requires confirmation via a broader
systematic review.

---

## 7. Synthesis — What Is PathKit's Actual Contribution?

| Candidate | Verdict |
|---|---|
| A new ML model | **No** — logistic regression over hand-engineered features is not novel |
| A new seven-class intent taxonomy | **Candidate** — granular, recon-oriented; novelty requires systematic review to confirm |
| A layered encoding-decode pipeline | **Candidate** — iterative URL→hex→base64 decoding is concrete and reusable, but prior art must be checked |
| A hybrid ordered decision pipeline | **Candidate** — rule-first pre-filter → ML applied to path intent; closest analog is cascade/pre-filter+ML |
| Self-supervised labeling with leakage control | **Incremental** — pattern exists; the held-out discipline is worth documenting |

### Contribution statement (one line)

> **PathKit's proposed contribution is an empirically validated *hybrid taxonomy
> and decision pipeline* — not a new model — that combines layered encoding
> decoding, identifier detection, and a linguistic classifier to distinguish
> semantic content paths from opaque system identifiers in reconnaissance data.
> (Novelty claim pending systematic review.)**

### Remaining work to substantiate this

- [ ] Verify each citation (URLNet, URLTran, etc.) against primary sources.
- [ ] Run a systematic search (Google Scholar, DBLP, arXiv) with defined queries
      to confirm whether any prior work defines the same 7-class intent taxonomy.
- [ ] Position against the closest architectural analog (cascade/pre-filter+ML).
- [ ] Add primary-source citations (not generic tool references) before manuscript.
