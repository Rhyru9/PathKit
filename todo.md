# PathKit Research and Publication Roadmap

Goal: turn PathKit into a reproducible, empirically validated research
artifact with a defensible novel contribution, then publish the results as an
arXiv paper and an archival code/data release.

---

## Progress Snapshot (updated 2026-06-13)

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
| Ground-truth (500 labeled) | done | `data/annotate/sample_labeled.csv` |
| Evaluation harness (P/R/F1/confusion/abstention) | done | `eval/harness.py` |
| Retrain + held-out eval (no leakage) | done | `scripts/retrain_eval.py` |

### Current results (500 held-out ground-truth)

```
Accuracy:  0.984
Macro F1:  0.99
```

| Class | F1 |
|---|---|
| asset | 1.00 |
| encoded | 1.00 |
| search | 1.00 |
| random_id | 0.99 |
| slug | 0.99 |
| file | 0.98 |

Progression: stale model 0.33 → retrained 0.65 → +detector gaps 0.78 →
+asset fix 0.85 → +file/asset rules 0.96 → +encoding layer 0.97 →
+num_dash rule **0.98**.

### Known remaining issues

- 6 slugs still misclassified as `file` (~3% of slugs).
- Ground truth has only 1 annotator (need 2nd for inter-annotator agreement).
- Dataset shrank to 22,583 paths; docs still reference 230,200 (stale).

---

## 1. Research direction

- [ ] **Defining the novel research contribution** *(not started)*
  - Formulate a precise claim that differentiates PathKit from regex-only
    endpoint parsing and generic URL classification.
  - Define research questions, hypotheses, intended users, and measurable
    success criteria.
- [ ] **Surveying related work and prior art** *(not started)*
  - Review URL classification, web crawling, endpoint discovery, semantic URL
    analysis, identifier detection, and security reconnaissance.
  - Build a comparison matrix and identify the exact research gap.

## 2. Dataset and annotation

- [ ] **Curating a reproducible URL path dataset** *(not started)*
  - Document sources, collection dates, licenses, normalization, deduplication,
    language distribution, and domain split.
  - Add versioned manifests and publish only sanitized, permitted data.
- [x] **Creating a human-verified ground-truth set** *(in progress)*
  - [x] Define annotation rules (slug/api/asset/search/random_id/file/encoded)
        -> `data/annotate/guidelines.md`
  - [x] Sample generator with fixed seed -> `scripts/sample_annotate.py`
  - [x] 500 paths labeled -> `data/annotate/sample_labeled.csv`
  - [ ] Add a 2nd annotator + measure inter-annotator agreement
  - [ ] Freeze the test set (never used for training)
- [x] **Preventing heuristic label leakage** *(done)*
  - [x] Held-out set excluded from training -> `scripts/retrain_eval.py`
        (trains on 22,083 auto-labeled, evaluates on 500 held-out)

## 3. Evaluation and scientific validation

- [x] **Building a rigorous evaluation harness** *(done)*
  - [x] Deterministic train/val/eval with fixed seed -> `eval/harness.py`
  - [x] Accuracy, per-class precision/recall/F1, macro/micro, confusion matrix,
        abstention -> `eval/harness.py`
  - [ ] Domain-held-out and temporal-held-out evaluation
- [ ] **Establishing strong baseline comparisons** *(not started)*
  - regex-only, majority, TF-IDF+logreg, tree-based, ML-only variants
- [ ] **Running detector and feature ablation studies** *(not started)*
  - Measure contribution of each detector, feature group, post-filter
- [ ] **Expanding context-aware path intent modeling** *(not started)*
- [ ] **Testing security reconnaissance usefulness** *(not started)*
- [x] **Analyzing errors and threats to validity** *(in progress)*
  - [x] Iteratively fixed: stale weights, random_id gap, asset gap, file gap,
        encoded/search gap via encoding layer
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
