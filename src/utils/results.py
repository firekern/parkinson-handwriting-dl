from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd


def save_results_csv(
    fold_scores: list[dict[str, float]],
    output_path: str | Path,
    extra_meta: dict | None = None,
    timestamp: bool = True,
) -> pd.DataFrame:
    """
    Persist fold scores to CSV, appending experiment metadata columns.

    When timestamp=True the filename gets a precise datetime suffix so
    every execution is tracked chronologically:
        results_xgboost_20260604_143022.csv

    Args:
        fold_scores: list of per-fold metric dicts.
        output_path:  destination CSV (parent dirs created automatically).
        extra_meta:   extra columns added to every row (e.g. exp name, seed).
        timestamp:    inject YYYYMMDD_HHMMSS before .csv suffix.

    Returns:
        The DataFrame that was written.
    """
    df = pd.DataFrame(fold_scores)

    if extra_meta:
        for k, v in extra_meta.items():
            df[k] = v

    output_path = Path(output_path)

    if timestamp:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_path.with_name(
            output_path.stem + f"_{ts}" + output_path.suffix
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return df
