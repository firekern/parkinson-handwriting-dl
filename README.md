# 99% Sure? Gabor Begs to Differ

Code and paper for **"99% Sure? Gabor Begs to Differ: A Time-Frequency Look at
Parkinson's Handwriting and a Structure-Preserving Image Encoding."**

We study Parkinson's disease (PD) detection from online handwriting on the public
**PaHaW** benchmark (72 subjects: 37 PD, 35 healthy controls). The paper makes three
points:

1. **Literature audit** — reported PaHaW accuracies (often >90%, sometimes 98–100%)
   are inflated by subject leakage, feature-selection bias, feature explosion, and the
   absence of variance/uncertainty in the reported numbers.
2. **A time-frequency limit** — the PD signature (a 4–6 Hz tremor interleaved with
   sub-decisecond pen arrests) is bounded by the Heisenberg–Gabor uncertainty
   principle (σ_t·σ_f ≥ 1/4π) *upstream* of any classifier, so no fixed representation
   can resolve both regimes on a short 150 Hz signal.
3. **A structure-preserving encoding** — instead of separating PD from healthy
   (ill-posed), we re-encode the kinematics of the Archimedean spiral (Task 1) as a
   colour image read by a **frozen ImageNet backbone** (ViT-B/16, Swin-T,
   EfficientNet-B0) and classified by a per-fold-tuned head.

Under repeated nested cross-validation with the **Nadeau–Bengio corrected t-test**,
the best encoding (effort, ViT, random forest) clears chance and a clinical baseline
(F1 0.7457 vs. 0.5080, p = 0.0187) — but no encoding is statistically separable from
its nearest rivals. The honest number on 72 subjects is a modest one.

The full paper is in [`paper/handwriting_uncertainty.pdf`](paper/handwriting_uncertainty.pdf).

---

## Project Structure

```
.
├── data/
│   ├── raw/                     # PaHaW source data (git-ignored)
│   └── processed/               # Cached renders + embeddings (git-ignored)
├── paper/
│   ├── handwriting_uncertainty.tex   # Paper source (self-contained: TikZ + tables)
│   ├── handwriting_uncertainty.pdf   # Compiled paper
│   ├── references.bib
│   ├── neurips_2023.sty / natbib.sty # Style files
└── src/
    ├── data/
    │   ├── pahaw.py             # load_subjects(), read_svc(), task_path()
    │   ├── features.py          # 33-dim handcrafted clinical feature vector
    │   └── trajectory_image.py  # spiral → colour image (10 modalities)
    ├── models/
    │   ├── image/vit_encoder.py # build_vit_encoder(), encode_image() (timm, frozen)
    │   └── heads/mlp.py         # FixedMLPClassifier, SmallMLPClassifier
    ├── experiments/grid_sweep/
    │   ├── generate_embeddings.py   # render images + cache frozen-backbone embeddings
    │   ├── param_grids.py           # head registry + grids (single-seed sweep)
    │   ├── param_grids_robust.py    # head registry + grids (repeated sweep)
    │   ├── run_all_heads.py         # input registry, subject-level metrics
    │   ├── run_repeated.py          # repeated nested 10×3 CV (seeds 42,43,44) ★
    │   ├── summarize_repeated.py    # aggregate repeated results
    │   └── results/                 # per-fold result CSVs (committed)
    ├── analysis/
    │   ├── nadeau_bengio.py     # corrected resampled paired t-test ★
    │   └── full_pairwise.py     # all-pairs significance table ★
    └── utils/
        ├── metrics.py           # classification_metrics(), aggregate_fold_scores()
        └── results.py           # save_results_csv()
```

★ = the three reproducibility scripts cited in the paper.

---

## Setup

```bash
uv sync
```

PaHaW is not redistributed here. Place the dataset under `data/raw/` (one folder per
subject, `<id>__<task>_1.svc` files) so that `src/data/pahaw.py:load_subjects()` can
find it.

---

## Reproducing the Paper

```bash
# 1. Render the 10 spiral image modalities and cache frozen-backbone embeddings
uv run python src/experiments/grid_sweep/generate_embeddings.py

# 2. Repeated nested 10×3 StratifiedGroupKFold CV (seeds 42, 43, 44) over all cells
uv run python src/experiments/grid_sweep/run_repeated.py

# 3. Aggregate the per-cell fold CSVs
uv run python src/experiments/grid_sweep/summarize_repeated.py

# 4. Significance testing (Nadeau–Bengio corrected t-test, all pairs)
uv run python src/analysis/full_pairwise.py
```

Results are written to `src/experiments/grid_sweep/results/all_heads_repeated/`.

---

## Evaluation Protocol

| Loop  | Folds | Splitter              | Purpose                          |
|-------|-------|-----------------------|----------------------------------|
| Outer | 10    | StratifiedGroupKFold  | Unbiased test-set evaluation     |
| Inner | 3     | StratifiedKFold       | Per-fold head hyperparameter tuning |

`StratifiedGroupKFold` (subject = group) preserves class balance **and** prevents
subject-level leakage. The protocol is repeated over **3 seeds (42, 43, 44)** → 30
test folds per cell. Model comparisons use the **Nadeau–Bengio corrected resampled
paired t-test**, which repairs the optimistic variance of the naive fold-wise test.

---

## Representations & Models

- **10 image modalities** of the spiral: 6 single-signal colour maps (velocity,
  acceleration, pressure, azimuth, altitude, effort), 3 RGB triplets
  (`rgb_vpa`, `rgb_vpe`, `rgb_vpz`), and 1 raw uncoloured stroke (geometry control).
- **3 frozen backbones**: ViT-B/16, Swin-T, EfficientNet-B0.
- **7 heads**: logistic regression, 3 SVMs, random forest, 2 MLPs.
- **Baseline**: 33-dim handcrafted clinical feature vector (Drotář et al., Impedovo).

In all: 31 inputs (10 modalities × 3 backbones + baseline) × 7 heads = 217 cells.

---

## Slides

A talk deck built with [open-slide](https://open-slide.dev/) lives in
`slides/pahaw-uncertainty/` (deck: `slides/pahaw-gabor/`, 20 pages).

```bash
cd slides/pahaw-uncertainty
npm install       # first time only
npm run dev       # live preview at localhost — press F to present, export PDF from the browser
npm run build     # static site → dist/
```

---

## Citation

```bibtex
@misc{porcelli2025gabor,
  title  = {99\% Sure? Gabor Begs to Differ: A Time-Frequency Look at
            Parkinson's Handwriting and a Structure-Preserving Image Encoding},
  author = {Porcelli, Andrea},
  year   = {2025},
}
```

---

## License

Released under the [MIT License](LICENSE). PaHaW is the property of its original
authors and is **not** redistributed in this repository.
