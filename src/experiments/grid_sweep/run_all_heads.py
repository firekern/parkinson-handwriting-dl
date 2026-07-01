"""
Full experiment grid: 51 input embeddings × 8 classification heads.

Input format: (N_subjects, 8, dim) — one vector per subject per task.

Evaluation protocol — Nested 10×3 StratifiedGroupKFold CV:
  Outer (10): StratifiedGroupKFold on task-level data, groups = subject index
              → all 8 tasks of the same subject always in the same split
  Inner (3):  GridSearchCV(cv=3, scoring='f1') on trainval tasks
  Metrics:    subject-level (task probabilities averaged per subject → threshold)

Run:
    uv run python src/experiments/grid_sweep/run_all_heads.py
    uv run python src/experiments/grid_sweep/run_all_heads.py --dry-run
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GridSearchCV, StratifiedGroupKFold
from sklearn.preprocessing import StandardScaler

from src.data.pahaw import load_subjects
from src.experiments.grid_sweep.generate_embeddings import (
    img_cache_path, hc_cache_path,
    IMAGE_BACKBONES, MODALITIES,
)
from src.experiments.grid_sweep.param_grids import HEAD_REGISTRY, build_estimator
from src.utils import classification_metrics, save_results_csv

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)

RESULTS_DIR = Path("src/experiments/grid_sweep/results/all_heads")


# Input registry -----------------------------------------------------------

def _short_backbone(backbone: str) -> str:
    if "efficientnet" in backbone:
        return "effnet"
    if "vit" in backbone:
        return "vit"
    if "swin" in backbone:
        return "swin"
    if "r2plus1d" in backbone:
        return "r2plus1d"
    if "r3d" in backbone:
        return "r3d"
    return backbone


def build_input_registry() -> dict[str, Path]:
    reg: dict[str, Path] = {}
    reg["handcrafted"] = hc_cache_path()
    for bb in IMAGE_BACKBONES:
        short = _short_backbone(bb)
        for mod in MODALITIES:
            reg[f"img_{mod}_{short}"] = img_cache_path(bb, mod)
    return reg


# Subject-level evaluation -------------------------------------------------

def subject_level_metrics(
    task_probs: np.ndarray,
    task_labels: np.ndarray,
    task_subjects: np.ndarray,
    y_subj: np.ndarray,
) -> dict[str, float]:
    """Average task probabilities per subject, then compute binary metrics."""
    unique_subj = np.unique(task_subjects)
    subj_probs = np.array([task_probs[task_subjects == s].mean() for s in unique_subj])
    subj_labels = np.array([y_subj[s] for s in unique_subj])
    pred = (subj_probs >= 0.5).astype(int)
    return classification_metrics(subj_labels, pred, subj_probs)


# Single experiment --------------------------------------------------------

def run_experiment(
    input_name: str,
    head_name: str,
    X_tasks: np.ndarray,   # (N_subjects, 8, dim)
    y: np.ndarray,         # (N_subjects,)
    groups: np.ndarray,    # (N_subjects,) = arange(N_subjects)
    seed: int = 42,
) -> list[dict]:
    n_subj, n_tasks, dim = X_tasks.shape

    # Flatten to task level
    X_flat = X_tasks.reshape(n_subj * n_tasks, dim)
    y_flat = np.repeat(y, n_tasks)
    groups_flat = np.repeat(groups, n_tasks)

    outer_cv = StratifiedGroupKFold(n_splits=10, shuffle=True, random_state=seed)
    param_grid = HEAD_REGISTRY[head_name]["param_grid"]
    fold_scores: list[dict] = []

    for fold_i, (trainval_idx, test_idx) in enumerate(
        outer_cv.split(X_flat, y_flat, groups_flat)
    ):
        scaler = StandardScaler()
        X_tr = scaler.fit_transform(X_flat[trainval_idx])
        X_te = scaler.transform(X_flat[test_idx])
        y_tr = y_flat[trainval_idx]

        estimator = build_estimator(head_name, seed=seed + fold_i)

        if param_grid:
            search = GridSearchCV(
                estimator, param_grid,
                cv=3, scoring="f1", n_jobs=-1, refit=True,
            )
            search.fit(X_tr, y_tr)
            best_clf = search.best_estimator_
        else:
            best_clf = estimator
            best_clf.fit(X_tr, y_tr)

        task_probs = best_clf.predict_proba(X_te)[:, 1]
        metrics = subject_level_metrics(
            task_probs, y_flat[test_idx],
            groups_flat[test_idx], y,
        )
        fold_scores.append({"outer_fold": fold_i, **metrics})

    return fold_scores


# Main ------------------------------------------------------------

def main(dry_run: bool = False) -> None:
    subject_ids, y, groups = load_subjects()
    log.info("Subjects: %d  PD=%d  HC=%d", len(y), y.sum(), (y == 0).sum())

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    INPUT_REGISTRY = build_input_registry()
    heads = list(HEAD_REGISTRY.keys())

    available = {n: p for n, p in INPUT_REGISTRY.items() if p.exists()}
    missing   = [n for n, p in INPUT_REGISTRY.items() if not p.exists()]
    if missing:
        log.warning("Missing embeddings (%d) — run generate_embeddings.py first", len(missing))
    log.info("Available inputs: %d/%d  |  Heads: %d  |  Total: %d",
             len(available), len(INPUT_REGISTRY), len(heads), len(available) * len(heads))

    total = len(available) * len(heads)
    done = 0
    summary_rows: list[dict] = []

    for input_name, cache_path in available.items():
        X_tasks = np.load(cache_path)   # (N_subj, 8, dim)
        # Task 1 only (index 0)
        X_tasks = X_tasks[:, 0:1, :]   # (N_subj, 1, dim)
        dim = X_tasks.shape[2]

        for head_name in heads:
            done += 1
            result_path = RESULTS_DIR / f"{input_name}__{head_name}.csv"

            if result_path.exists():
                log.info("[%d/%d] Skip: %s × %s", done, total, input_name, head_name)
                continue

            log.info("[%d/%d] %s × %s  (dim=%d)", done, total, input_name, head_name, dim)
            if dry_run:
                continue

            fold_scores = run_experiment(input_name, head_name, X_tasks, y, groups)
            save_results_csv(
                fold_scores, result_path,
                extra_meta={"input": input_name, "head": head_name, "dim": dim},
                timestamp=False,
            )

            means = {k: float(np.mean([s[k] for s in fold_scores]))
                     for k in fold_scores[0] if k != "outer_fold"}
            stds  = {k: float(np.std([s[k]  for s in fold_scores], ddof=1))
                     for k in fold_scores[0] if k != "outer_fold"}
            log.info("  → F1=%.3f±%.3f  AUC=%.3f±%.3f",
                     means.get("test_f1", 0), stds.get("test_f1", 0),
                     means.get("test_auc", 0), stds.get("test_auc", 0))
            summary_rows.append({"input": input_name, "head": head_name, "dim": dim,
                                  **means, "std_f1": stds.get("test_f1", 0),
                                  "std_auc": stds.get("test_auc", 0)})

    if summary_rows and not dry_run:
        summary = pd.DataFrame(summary_rows).sort_values("test_f1", ascending=False)
        summary.to_csv(RESULTS_DIR / "summary.csv", index=False)
        log.info("\nTop-10 by mean F1:")
        for _, row in summary.head(10).iterrows():
            log.info("  %-35s × %-20s  F1=%.3f±%.3f  AUC=%.3f",
                     row["input"], row["head"],
                     row["test_f1"], row["std_f1"], row["test_auc"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
