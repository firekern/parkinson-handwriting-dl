"""
Repeated nested cross-validation sweep — the *robust* re-evaluation.

Protocol (per (input, head) cell):
  Repeats (R=3):  seeds 42, 43, 44 — independent shuffles of the outer split.
  Outer (10):     StratifiedGroupKFold, groups = subject  → no subject leakage.
  Inner (3):      GridSearchCV(scoring='f1') over the anti-overfitting grids in
                  ``param_grids_robust`` → the winning HP is recorded per fold.
  Metrics:        subject-level (task probabilities averaged per subject).

Output:  one CSV per cell in ``results/all_heads_repeated/`` with 30 rows
         (3 repeats x 10 folds), each carrying its winning hyper-parameters.

Parallelism:  a process pool runs one whole cell per task; every worker keeps
              BLAS/torch single-threaded so the pool — not the estimators —
              owns the cores. MLP heads use the GPU. Resumable: existing CSVs
              are skipped.

Run:
    uv run python -m src.experiments.grid_sweep.run_repeated            # full
    uv run python -m src.experiments.grid_sweep.run_repeated --workers 10
    uv run python -m src.experiments.grid_sweep.run_repeated --dry-run
    uv run python -m src.experiments.grid_sweep.run_repeated --heads mlp_small random_forest
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

# Single-thread the math libs *before* numpy/torch import so the process pool
# (not the estimators) owns parallelism. Inherited by spawned workers.
for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
           "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

SEEDS = [42, 43, 44]                      # R = 3 repeats
RESULTS_DIR = Path("src/experiments/grid_sweep/results/all_heads_repeated")
METRIC_KEYS = (
    "test_accuracy", "test_f1", "test_auc",
    "test_precision", "test_recall", "test_specificity",
)


# --- one cell (input x head), all repeats -------------------------------------

def run_cell(input_name: str, cache_path: str, head_name: str,
             seeds: list[int]) -> list[dict]:
    """Run R repeats of nested 10x3-fold CV for one cell; return 30 fold rows."""
    import torch
    from sklearn.model_selection import GridSearchCV, StratifiedGroupKFold
    from sklearn.preprocessing import StandardScaler

    from src.data.pahaw import load_subjects
    from src.experiments.grid_sweep.param_grids_robust import (
        ROBUST_HEAD_REGISTRY, build_robust_estimator,
    )
    from src.experiments.grid_sweep.run_all_heads import subject_level_metrics

    torch.set_num_threads(1)
    _, y, groups = load_subjects()

    X_tasks = np.load(cache_path)[:, 0:1, :]          # (N, 1, dim) — Task 1
    n_subj, n_tasks, dim = X_tasks.shape
    X_flat = X_tasks.reshape(n_subj * n_tasks, dim)
    y_flat = np.repeat(y, n_tasks)
    groups_flat = np.repeat(groups, n_tasks)
    param_grid = ROBUST_HEAD_REGISTRY[head_name]["param_grid"]

    rows: list[dict] = []
    for rep, seed in enumerate(seeds):
        outer_cv = StratifiedGroupKFold(n_splits=10, shuffle=True, random_state=seed)
        for fold_i, (tr, te) in enumerate(outer_cv.split(X_flat, y_flat, groups_flat)):
            scaler = StandardScaler()
            X_tr = scaler.fit_transform(X_flat[tr])
            X_te = scaler.transform(X_flat[te])
            y_tr = y_flat[tr]

            estimator = build_robust_estimator(head_name, seed=seed + fold_i)
            search = GridSearchCV(
                estimator, param_grid, cv=3, scoring="f1", n_jobs=1, refit=True,
            )
            search.fit(X_tr, y_tr)
            best = search.best_estimator_

            task_probs = best.predict_proba(X_te)[:, 1]
            metrics = subject_level_metrics(task_probs, y_flat[te], groups_flat[te], y)
            rows.append({
                "repeat": rep, "seed": seed, "outer_fold": fold_i,
                **{k: metrics[k] for k in METRIC_KEYS},
                "best_params": json.dumps(search.best_params_, sort_keys=True),
            })
    return rows


def _worker(task: tuple) -> tuple[str, str, str | None]:
    """Pool entry point: run a cell, write its CSV, return (cell, status)."""
    input_name, cache_path, head_name, dim = task
    out = RESULTS_DIR / f"{input_name}__{head_name}.csv"
    try:
        rows = run_cell(input_name, cache_path, head_name, SEEDS)
        df = pd.DataFrame(rows)
        df.insert(0, "head", head_name)
        df.insert(0, "input", input_name)
        df["dim"] = dim
        df.to_csv(out, index=False)
        f1 = df["test_f1"].mean()
        return (f"{input_name}__{head_name}", "ok", f"F1={f1:.3f}")
    except Exception as exc:  # noqa: BLE001 — record, keep the sweep alive
        return (f"{input_name}__{head_name}", "ERROR", repr(exc))


# --- orchestration ------------------------------------------------------------

def build_tasks(heads: list[str], inputs: list[str] | None) -> list[tuple]:
    from src.experiments.grid_sweep.run_all_heads import build_input_registry
    registry = build_input_registry()
    tasks: list[tuple] = []
    for name, path in registry.items():
        if inputs and name not in inputs:
            continue
        if not path.exists():
            continue
        dim = int(np.load(path, mmap_mode="r").shape[2])
        for head in heads:
            out = RESULTS_DIR / f"{name}__{head}.csv"
            if out.exists():
                continue
            tasks.append((name, str(path), head, dim))
    return tasks


def main() -> None:
    from src.experiments.grid_sweep.param_grids_robust import ROBUST_HEAD_REGISTRY

    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--heads", nargs="*", default=list(ROBUST_HEAD_REGISTRY))
    ap.add_argument("--inputs", nargs="*", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    tasks = build_tasks(args.heads, args.inputs)
    print(f"Cells to run: {len(tasks)}  |  repeats={len(SEEDS)}  "
          f"|  workers={args.workers}  |  heads={args.heads}", flush=True)
    if args.dry_run or not tasks:
        for t in tasks:
            print("  ", t[0], t[2], f"dim={t[3]}")
        return

    import multiprocessing as mp
    from concurrent.futures import ProcessPoolExecutor, as_completed
    from tqdm import tqdm

    ctx = mp.get_context("spawn")
    errors: list[tuple] = []
    with ProcessPoolExecutor(max_workers=args.workers, mp_context=ctx) as ex:
        futs = {ex.submit(_worker, t): t for t in tasks}
        bar = tqdm(as_completed(futs), total=len(futs), ncols=100, desc="cells")
        for fut in bar:
            cell, status, info = fut.result()
            if status == "ERROR":
                errors.append((cell, info))
                bar.write(f"[ERROR] {cell}: {info}")
            else:
                bar.write(f"[ok] {cell}  {info}")

    print(f"\nDone. {len(tasks) - len(errors)}/{len(tasks)} ok, {len(errors)} errors.")
    for cell, info in errors:
        print("  ERROR", cell, info)


if __name__ == "__main__":
    main()
