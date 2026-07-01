from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    auc,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def classification_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray,
) -> dict[str, float]:
    """Return accuracy, f1, auc, precision, recall, specificity."""
    tn_fp = np.sum((y_true == 0))
    fn_tn = np.sum((y_pred == 0))
    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    return {
        "test_accuracy": float(accuracy_score(y_true, y_pred)),
        "test_f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "test_auc": float(roc_auc_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else 0.0,
        "test_precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "test_recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "test_specificity": float(specificity),
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }


def aggregate_fold_scores(fold_scores: list[dict[str, float]]) -> dict[str, dict[str, float]]:
    """
    Compute mean ± std for each metric across folds.

    Returns:
        {"mean": {metric: value}, "std": {metric: value}}
    """
    if not fold_scores:
        return {"mean": {}, "std": {}}

    metric_keys = [k for k in fold_scores[0] if k not in ("fold", "outer_fold", "seed")]
    mean: dict[str, float] = {}
    std: dict[str, float] = {}

    for k in metric_keys:
        values = [s[k] for s in fold_scores if k in s]
        arr = np.array(values, dtype=float)
        mean[k] = float(arr.mean())
        std[k] = float(arr.std(ddof=1) if len(arr) > 1 else 0.0)

    return {"mean": mean, "std": std}


def compute_summary_table(
    fold_scores: list[dict[str, float]],
    metric_names: list[str] | None = None,
) -> pd.DataFrame:
    """
    Build a DataFrame with one row per fold plus a Mean ± Std footer.

    Args:
        fold_scores: list of per-fold metric dicts.
        metric_names: columns to include; None = all numeric columns.

    Returns:
        DataFrame with columns [fold, *metrics] and two extra rows: mean, std.
    """
    df = pd.DataFrame(fold_scores)

    if metric_names:
        cols = [c for c in ["fold", "outer_fold", "seed"] if c in df.columns]
        cols += [m for m in metric_names if m in df.columns]
        df = df[cols]

    agg = aggregate_fold_scores(fold_scores)
    mean_row = {"fold": "mean", **agg["mean"]}
    std_row = {"fold": "std", **agg["std"]}

    summary = pd.concat(
        [df, pd.DataFrame([mean_row, std_row])],
        ignore_index=True,
    )
    return summary
