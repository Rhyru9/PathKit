# PathKit — Research Contribution Definition

> This document locks the research positioning. It defines the claim, the
> research questions, testable hypotheses, output taxonomy, success metrics,
> and — critically — the boundaries of what PathKit does *not* claim.

---

## 1. Main Claim (one paragraph)

PathKit is a **hybrid framework** that combines (a) structure-based identifier
detectors, (b) layered encoding detection and iterative decoding, and (c) a
linguistic/structural feature classifier to distinguish **semantic content
paths** (human-readable slugs) from **opaque/system identifiers** (UUIDs,
timestamps, hashes, base64 tokens, internal routing codes) in web URL path
tokens.

The core contribution is **not** a new model architecture — it is the
**decomposition of URL path intent into a seven-class taxonomy** plus the
**ordering of decoding → rule-based detection → learned classification** that
makes the distinction robust and reproducible on real-world crawled data.

---

## 2. Research Questions

- **RQ1 (Accuracy).** Does a hybrid rule-based + feature-based pipeline
  classify URL path tokens into intent classes more accurately than either
  rule-only or ML-only approaches in isolation?

- **RQ2 (Encoding).** To what extent does *layered encoding detection and
  iterative decoding* (URL-encode, in-path hex, base64) improve classification
  of encoded tokens, and how prevalent are such tokens in real crawls?

- **RQ3 (Detector contribution).** What is the individual contribution of
  each identifier detector (UUID, timestamp, hash, base64, routing code) to
  overall accuracy, precision, and abstention rate?

---

## 3. Testable Hypotheses

- **H1.** The hybrid pipeline achieves higher macro-F1 on held-out path tokens
  than a rule-only baseline and an ML-only baseline, using identical splits.

- **H2.** Iterative decoding before classification yields a statistically
  significant accuracy gain on the subset of tokens that use any encoding.

- **H3.** Identifier detectors contribute a measurable accuracy gain by
  pre-filtering opaque tokens with high precision (they remove the "easy"
  non-slug cases that would otherwise confuse the ML classifier).

- **H4 (nullable).** A single-token linguistic classifier without URL
  *context* underperforms on ambiguous cases (e.g. `123-post-title` vs
  `8253-2`), motivating the need for context-aware modeling.

---

## 4. Output Class Taxonomy (7 classes)

| Class | Semantic meaning | Canonical examples |
|---|---|---|
| `slug` | Human-readable content / title / category | `panduan-belajar-online` |
| `api` | Programmatic endpoint / data object | `/api/v1/users/123`, `/log/1718201234` |
| `asset` | Static web asset (JS/CSS/CDN) | `main-9e107d.js`, `axios.min.js` |
| `search` | Query / filter string | `?q=sekolah&page=2` |
| `random_id` | Opaque identifier (UUID/hash/numeric/code) | `550e8400-e29b-…`, `P9996589` |
| `file` | Document / downloadable file | `laporan-2026.pdf`, `data.xml` |
| `encoded` | Encoded payload / delimiter-encoded token | `eyJpdiI6…`, `=3A=3A=3A` |

**Decision priority** (first match wins):

```
encoded → search → uuid → timestamp → hash → base64
→ other (org_unit, id_code, version, numeric, random_alnum,
         num_dash, static_asset, file_ext) → ML slug classifier
```

---

## 5. Success Metrics

Primary (class-balanced, reported per-class and aggregate):

- **Macro-F1** — primary metric (classes are highly imbalanced).
- **Accuracy** — secondary, reported for interpretability.
- **Per-class precision / recall / F1** — to expose class-specific weaknesses.
- **Abstention rate** — fraction of predictions flagged "uncertain"
  (confidence < 0.55 or top-2 margin < 0.08); a proxy for deployment safety.

Evaluation protocol:

- Deterministic seed; the held-out set is **never** used for auto-labeling or
  training in `scripts/retrain_eval.py`.
- `eval/harness.py` reports a deterministic train/validation split; the
  retraining script reports the separate 500-row held-out evaluation.
- Results must include support counts and confidence intervals; a class with
  zero support cannot support a performance claim.
- Current reproduction is descriptive only: accuracy `0.9780`, macro-F1
  `0.9072`; search recall is `0.3333`, and API has zero held-out support.

---

## 6. Claim Boundaries (anti-overclaim)

PathKit does **not** claim:

1. **Generality across domains.** Current evidence is a single Indonesian
   government/education crawl. Transfer to e-commerce, social media, or other
   locales is untested.

2. **Fully human-verified ground truth.** Training labels are self-supervised
   (heuristic). The current 500-row held-out sample was produced with
   heuristic assistance and reviewed by one annotator; inter-annotator
   agreement has not yet been measured.

3. **Security efficacy.** PathKit is a *classification aid*. It has not been
   shown to improve vulnerability discovery, coverage, or analyst throughput.

4. **Exhaustive taxonomy.** The seven classes cover observed data; a real
   deployment may require a `hybrid`/`ambiguous` output, which is currently
   only approximated via the abstention gate.

5. **Novel ML.** The classifier is logistic regression over hand-engineered
   features. Novelty lies in the decomposition + pipeline, not the estimator.

---

## 7. What Constitutes "Done" for this Phase

- [x] Seven-class taxonomy with decision priority defined.
- [x] Three research questions + four testable hypotheses stated.
- [x] Primary/secondary metrics and evaluation protocol fixed.
- [x] Current reproduced metrics and unsupported-class caveats recorded.
- [x] Claim boundaries written to prevent overclaiming.
- [ ] Every hypothesis mapped to a concrete experiment in `eval/` or
      `baselines/` (next phase).

## 8. Initial baseline result

The initial benchmark is implemented in `eval/baselines.py` and evaluates
majority, rule-only, ML-only, and hybrid variants on the same 500-row
development-held-out split. With the canonical production labeling and
decoding protocol, the hybrid system reaches accuracy `0.9760` and macro-F1
`0.9064`, versus `0.5640` / `0.6828` for rule-only, `0.7060` / `0.4108` for
ML-only, and `0.3440` / `0.0853` for majority. The key evidence is per-class:
rule-only scores `0.0` F1 on slug (cannot read content) while ML-only scores
`0.0` F1 on asset/encoded/random_id (cannot detect identifiers); only the
hybrid scores high on both. These results are not final paper evidence: the
split is heuristic-assisted, single-annotator, and has zero API support.

## 9. Initial ablation result

`eval/ablations.py` reuses the canonical decision flow and evaluates detector
removals on the same development-held-out split. The full hybrid reaches
accuracy `0.9780` and macro-F1 `0.9072`; removing the `other` detector reduces
accuracy to `0.7180` and macro-F1 to `0.6629`, while removing the routing
encoding detector reduces macro-F1 to `0.7393`. Removing UUID, timestamp, or
hash/Base64 stages produces no change on this split because those token types
are inadequately represented. These are descriptive development results, not
causal or final-paper estimates; the ablation must be repeated on a clean,
independently annotated test set.
