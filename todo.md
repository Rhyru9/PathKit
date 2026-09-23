# PathKit Research and Publication Roadmap

Goal: turn PathKit into a reproducible, empirically validated research
artifact with a defensible novel contribution, then publish the results as an
arXiv paper and an archival code/data release.

---

## Progress Snapshot (updated 2026-09-23)

> This section is the live status. Checkboxes below are the canonical tracker.

### Architecture (built & working)

| Component | Status | Location |
|---|---|---|
| 5 identifier detectors | done | `models/{uuid,timestamp,hash,base64,other}/` |
| Encoding detection + decode layer | done | `models/encoding/` |
| Slug ML classifier (24 features, 7 classes) | done | `models/slugs/` |
| CLI | done | `main.py` |

### Evaluation (built & working)

| Component | Status | Location |
|---|---|---|
| Annotation guidelines | done | `data/annotate/guidelines.md` |
| Sample generator (seeded) | done | `scripts/sample_annotate.py` |
| Auto-labeling + manual overrides | done | `scripts/label_annotate.py` |
| Held-out annotation sample (500 labeled) | in progress | `data/annotate/sample_labeled.csv` |
| Evaluation harness (P/R/F1/confusion/abstention) | done | `eval/harness.py` |
| Retrain + held-out eval (no leakage) | done | `scripts/retrain_eval.py` |

### Reproduced current results (500 held-out rows)

```
Accuracy:  0.9860
Macro F1:  0.9924
```

| Class | F1 |
|---|---|
| asset | 1.00 |
| encoded | 1.00 |
| search | 1.00 |
| random_id | 0.99 |
| slug | 0.9857 |
| file | 0.9716 |

These are descriptive results, not final paper evidence: the sample is
single-annotator and several classes are underrepresented. The `api` class has
zero held-out examples, so no claim about API performance is currently valid.

### Known remaining issues

- Ground truth labels were produced with heuristic assistance and reviewed by
  only 1 annotator (need a second annotator and agreement measurement).
- Dataset is 22,583 paths / 447,266 endpoints; provenance is documented in
  `paper/dataset.md`. Stale 230,200 references removed.
- Search recall is 1.0000 on the development-held-out split after fixing
  percent-encoded query decoding; clean-test confirmation is still required.
- No held-out `api` examples — API performance is unmeasured, not claimed.

---

## 1. Research direction

- [x] **Defining the novel research contribution** *(done)*
  - [x] Main claim: hybrid framework (structure detectors + layered decoding
        + linguistic classifier) for 7-class URL path intent
        -> `paper/contributions.md`
  - [x] 3 research questions (accuracy, encoding, detector contribution)
  - [x] 4 testable hypotheses (H1-H4)
  - [x] 7-class taxonomy + decision priority
  - [x] Success metrics (macro-F1 primary, per-class, abstention)
  - [x] Claim boundaries (5 anti-overclaim statements)
- [x] **Surveying related work and prior art** *(initial matrix done)*
  - [x] 6-category comparison matrix -> `paper/related-work.md`
        (URL classification, semantic URL, crawling/discovery, identifier
        classification, security recon, hybrid rule+ML)
  - [x] Contribution verdict: hybrid taxonomy + decision pipeline (not a model)
  - [ ] Verify individual citations (URLNet, URLTran, etc.) against primary sources

## 2. Dataset and annotation

- [ ] **Curating a reproducible URL path dataset** *(in progress — NOT done)*
  - [x] Source/context/counts/dates/language/domain/dedup -> `paper/dataset.md`
  - [x] Machine-readable manifest with hashes + reconciliation
        -> `data/manifest.json` (via `scripts/freeze_dataset.py`)
  - [x] Reconciled 22,583 paths vs 447,266 endpoints (94.5% overlap)
  - [x] Stale 230,200 references removed
  - [ ] Re-record exact crawl parameters (tool version, seed URLs, depth)
  - [ ] License verification (blocked — source ToS unknown)
  - [x] PII audit + documentation -> `paper/pii-audit.md`, `scripts/audit_pii.py`
  - [x] Sanitization script -> `scripts/sanitize_dataset.py`
        (produces `data/sanitized/*`; 908 NIP/name candidates, 2,067 ID
        codes, and 6 credential rows across both inputs; email counts overlap
        credential rows)
  - [ ] A clean, independently-annotated test set (current is development-held-out)
- [ ] **Creating a human-verified ground-truth set** *(in progress — human-blocked)*
  - [x] Define annotation rules (slug/api/asset/search/random_id/file/encoded)
        -> `data/annotate/guidelines.md`
  - [x] Clean test-set sampler (fresh seed=2026, 600 rows, api/search/encoded
        oversampled) -> `scripts/sample_clean_test.py`
  - [x] Clean test set generated -> `data/annotate/clean_test.csv` (heuristic
        first-pass in `label_a`; automated diagnostic `label_b` is not human
        ground truth)
  - [x] Cohen's kappa calculator -> `scripts/agreement.py`
  - [ ] Annotator 1 reviews `label_a` first-pass suggestions independently
        (heuristic-assisted; not ground truth and not a substitute for manual
        annotation)
  - [ ] Annotator 2 fills `label_b` (independent)
  - [ ] Run `scripts/agreement.py` -> measure Cohen's kappa
  - [ ] Adjudicate disagreements
  - [x] Expert-assisted adjudication stored in `label_final`; pre-adjudication
        κ=`0.8109`, 87 conflicts; independent third-annotator status not claimed
  - [x] Freeze metadata/hash -> `data/frozen/clean_test_metadata.json`
  - Note: the old 500 (`sample_labeled.csv`) remains development-held-out only.
- [x] **Preventing heuristic label leakage** *(done)*
  - [x] Current development-held-out set excluded from training -> `scripts/retrain_eval.py`
        (trains on 16,581 auto-labeled, evaluates on 500 held-out after the
        query-decoding fix)

## 3. Evaluation and scientific validation

- [x] **Building a rigorous evaluation harness** *(implemented; validation pending)*
  - [x] Deterministic train/val/eval with fixed seed -> `eval/harness.py`
  - [x] Accuracy, per-class precision/recall/F1, macro/micro, confusion matrix,
        abstention -> `eval/harness.py`
  - [x] Canonical classifier shared by CLI and evaluation -> `models/decision.py`
  - [x] URL/query-safe UTF-8 decoding regression coverage
  - [ ] Domain-held-out and temporal-held-out evaluation
  - [x] Endpoint control run completed: training on `endpoints.txt` reaches
        only `0.5867` accuracy / `0.5760` macro-F1 on clean endpoints;
        endpoint-context modeling is required before any generalization claim.
  - [x] Dedicated weak-label validation metadata -> `data/splits.json`
        (3,316 rows, seed=2027; raw CSV remains ignored)
- [x] **Establishing initial baseline comparisons** *(implemented; clean test pending)*
  - majority, rule-only, ML-only, and hybrid on identical 500-row split
  - `eval/baselines.py` uses the canonical production labeling/decoding path
  - Current result: hybrid accuracy `0.9860`, macro-F1 `0.9924`; API remains
    unsupported because the held-out set has zero API examples
  - [x] Add TF-IDF/logistic and tree-based supervised baselines
        -> `eval/supervised_baselines.py` (development split only)
- [x] **Running initial detector ablation study** *(implemented; clean test pending)*
  - `eval/ablations.py` measures full hybrid, detector removals, rule-only,
    and ML-only on the identical development-held-out split.
  - Full hybrid: accuracy `0.9860`, macro-F1 `0.9924`; removing `other` drops
    accuracy to `0.7260`, while removing encoding drops macro-F1 to `0.8244`.
  - UUID/timestamp/hash/Base64 deltas are zero on this split because coverage
    is inadequate; this is not evidence those detectors are unnecessary.
  - [ ] Repeat on an independently annotated test set with adequate detector
    coverage and add feature/runtime ablations.
- [ ] **Expanding context-aware path intent modeling** *(not started)*
- [ ] **Testing security reconnaissance usefulness** *(not started)*
- [x] **Analyzing errors and threats to validity** *(in progress)*
  - [x] Fixed decoder corruption, CLI/evaluation divergence, and training
        leakage in the evaluation harness
  - [x] Reproduced current error profile (notably weak search recall)
  - [ ] Document limitations, dataset bias, privacy, abstention conditions

## 4. Reproducibility and release

- [ ] **Hardening the reproducible research release** *(in progress)*
  - [x] Seeded sample + retrain + eval scripts
  - [ ] Dataset manifest, experiment config, benchmark runner, versioned artifacts
  - [ ] Reconcile README/flow-system counts with current 22,583 dataset (stale)
- [ ] **Preparing public code and artifact release** *(not started)*
  - GitHub release + Zenodo DOI, license/citation metadata, sanitized data

## 5. Manuscript and publication

- [ ] **Writing the arXiv manuscript** *(not started)*
- [ ] **Conducting an internal pre-submission review** *(not started)*
- [ ] **Submitting the arXiv-ready version** *(not started)*

## Proposed paper direction

**Working title:** *PathKit: A Hybrid Rule-Based and Feature-Based Framework
for URL Path Token Intent Classification*

The paper should be positioned as an empirical systems study unless the
context-aware extension demonstrates a clearly novel and reproducible method.
