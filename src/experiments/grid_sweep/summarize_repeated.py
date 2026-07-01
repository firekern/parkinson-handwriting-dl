"""
Summarise the repeated nested-CV sweep.

Builds, from ``results/all_heads_repeated/*.csv``:
  * ``summary.csv`` — one row per (input, head): mean/std of every metric over
    the 30 folds, plus the modal winning hyper-parameter and its frequency.
  * prints the top-N ranking (best head per input) for a chosen metric.

Run:
    uv run python -m src.experiments.grid_sweep.summarize_repeated --metric test_f1
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

RESULTS_DIR = Path("src/experiments/grid_sweep/results/all_heads_repeated")
METRICS = ("test_f1", "test_auc", "test_accuracy",
           "test_precision", "test_recall", "test_specificity")


def modal_params(series: pd.Series) -> tuple[str, int, int]:
    """Return (modal best_params json, its count, n_distinct)."""
    c = Counter(series.tolist())
    (best, cnt), = c.most_common(1)
    return best, cnt, len(c)


def build_summary() -> pd.DataFrame:
    rows = []
    for f in sorted(RESULTS_DIR.glob("*__*.csv")):
        if f.name == "summary.csv":
            continue
        df = pd.read_csv(f)
        inp, head = f.stem.split("__", 1)
        rec = {"input": inp, "head": head, "n_folds": len(df),
               "dim": int(df["dim"].iloc[0]) if "dim" in df else -1}
        for m in METRICS:
            rec[f"{m}_mean"] = float(df[m].mean())
            rec[f"{m}_std"] = float(df[m].std(ddof=1))
        modal, cnt, ndist = modal_params(df["best_params"])
        rec["best_param_modal"] = modal
        rec["best_param_freq"] = f"{cnt}/{len(df)}"
        rec["best_param_ndistinct"] = ndist
        rows.append(rec)
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--metric", default="test_f1")
    ap.add_argument("--top", type=int, default=15)
    args = ap.parse_args()

    summary = build_summary()
    if summary.empty:
        print("No results yet in", RESULTS_DIR)
        return
    summary = summary.sort_values(f"{args.metric}_mean", ascending=False)
    summary.to_csv(RESULTS_DIR / "summary.csv", index=False)
    print(f"Cells summarised: {len(summary)}  →  {RESULTS_DIR/'summary.csv'}\n")

    # best head per input
    idx = summary.groupby("input")[f"{args.metric}_mean"].idxmax()
    bhpi = summary.loc[idx].sort_values(f"{args.metric}_mean", ascending=False)

    m = args.metric
    print(f"Top-{args.top} representations (best head each) by {m}:")
    print(f"{'input':28s} {'head':20s} {'mean±std':>16}  {'AUC':>6}  bestparam (freq)")
    print("-" * 100)
    for _, r in bhpi.head(args.top).iterrows():
        bp = json.loads(r["best_param_modal"])
        bp_s = ",".join(f"{k}={v}" for k, v in bp.items())
        print(f"{r['input']:28s} {r['head']:20s} "
              f"{r[m+'_mean']:.3f}±{r[m+'_std']:.3f}  {r['test_auc_mean']:6.3f}  "
              f"{bp_s} ({r['best_param_freq']})")


if __name__ == "__main__":
    main()
