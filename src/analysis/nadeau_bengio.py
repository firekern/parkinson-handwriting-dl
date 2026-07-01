"""
Nadeau & Bengio (2003) corrected resampled paired t-test.

Standard paired t-tests across cross-validation folds are *anti-conservative*:
because training sets overlap heavily between folds, the per-fold score
differences are positively correlated, so the naive variance estimate is too
small and p-values are optimistic. Nadeau & Bengio correct the variance by the
factor ``(1/N + n_test/n_train)`` instead of ``1/N``:

    t = mean(d) / sqrt( (1/N + rho/(1-rho)) * var(d) ) ,   df = N - 1

with N = number of folds (here R x k = 3 x 10 = 30), ``rho`` = test fraction
(= 1/k for k-fold) so ``rho/(1-rho) = 1/(k-1)``. We pair on identical folds:
both models share the same seeds and StratifiedGroupKFold splits, so fold
(repeat, outer_fold) indexes the *same* subjects for every model.

Reference: C. Nadeau, Y. Bengio, "Inference for the Generalization Error",
Machine Learning 52 (2003) 239-281.

CLI:
    uv run python -m src.analysis.nadeau_bengio --metric test_f1
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

RESULTS_DIR = Path("src/experiments/grid_sweep/results/all_heads_repeated")
N_FOLDS_PER_REPEAT = 10        # k
FOLD_KEY = ["seed", "outer_fold"]


@dataclass
class TestResult:
    name_a: str
    name_b: str
    mean_a: float
    mean_b: float
    mean_diff: float
    t_stat: float
    p_value: float
    df: int
    n: int


def corrected_resampled_ttest(
    diffs: np.ndarray, k_folds: int = N_FOLDS_PER_REPEAT,
) -> tuple[float, float, int]:
    """Return (t, two-sided p, df) for the Nadeau-Bengio corrected t-test.

    ``diffs`` are paired per-fold score differences (model A - model B).
    The correction factor is ``1/N + 1/(k-1)`` (test/train ratio for k-fold).
    """
    diffs = np.asarray(diffs, dtype=float)
    n = diffs.size
    df = n - 1
    mean_d = diffs.mean()
    var_d = diffs.var(ddof=1)
    if var_d == 0.0:
        return (0.0, 1.0, df)
    correction = 1.0 / n + 1.0 / (k_folds - 1)        # Nadeau-Bengio
    t_stat = mean_d / np.sqrt(correction * var_d)
    p = 2.0 * stats.t.sf(abs(t_stat), df)
    return (float(t_stat), float(p), df)


def load_cell(input_name: str, head: str) -> pd.DataFrame:
    df = pd.read_csv(RESULTS_DIR / f"{input_name}__{head}.csv")
    return df.sort_values(FOLD_KEY).reset_index(drop=True)


def paired_test(input_a: str, head_a: str, input_b: str, head_b: str,
                metric: str = "test_f1") -> TestResult:
    """Corrected paired t-test between two cells on a metric, aligned by fold."""
    a = load_cell(input_a, head_a)
    b = load_cell(input_b, head_b)
    merged = a.merge(b, on=FOLD_KEY, suffixes=("_a", "_b"))
    if len(merged) != len(a):
        raise ValueError(f"fold mismatch: {len(merged)} vs {len(a)} — "
                         "cells must share the same seeds/folds")
    diffs = (merged[f"{metric}_a"] - merged[f"{metric}_b"]).to_numpy()
    t, p, df = corrected_resampled_ttest(diffs)
    return TestResult(
        name_a=f"{input_a}/{head_a}", name_b=f"{input_b}/{head_b}",
        mean_a=float(merged[f"{metric}_a"].mean()),
        mean_b=float(merged[f"{metric}_b"].mean()),
        mean_diff=float(diffs.mean()), t_stat=t, p_value=p, df=df, n=len(diffs),
    )


# --- ranking helpers ----------------------------------------------------------

def best_head_per_input(metric: str = "test_f1") -> pd.DataFrame:
    """Mean metric per cell; keep the best head per input. Sorted desc."""
    rows = []
    for f in RESULTS_DIR.glob("*__*.csv"):
        if f.name == "summary.csv":
            continue
        df = pd.read_csv(f)
        inp, head = f.stem.split("__", 1)
        rows.append({"input": inp, "head": head,
                     "mean": df[metric].mean(), "std": df[metric].std(ddof=1)})
    full = pd.DataFrame(rows)
    idx = full.groupby("input")["mean"].idxmax()
    return full.loc[idx].sort_values("mean", ascending=False).reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--metric", default="test_f1")
    ap.add_argument("--top", type=int, default=12,
                    help="compare champion vs the next N representations")
    args = ap.parse_args()

    ranking = best_head_per_input(args.metric)
    if ranking.empty:
        print("No repeated results found in", RESULTS_DIR)
        return

    champ = ranking.iloc[0]
    print(f"\nChampion: {champ['input']}/{champ['head']}  "
          f"{args.metric}={champ['mean']:.3f}±{champ['std']:.3f}\n")
    print(f"{'vs representation/head':40s} {'meanΔ':>8} {'t':>7} {'p(corr)':>9} sig")
    print("-" * 72)

    out_rows = []
    for _, row in ranking.iloc[1:args.top + 1].iterrows():
        res = paired_test(champ["input"], champ["head"],
                          row["input"], row["head"], args.metric)
        sig = "*" if res.p_value < 0.05 else "ns"
        print(f"{res.name_b:40s} {res.mean_diff:+8.3f} {res.t_stat:7.2f} "
              f"{res.p_value:9.3f} {sig}")
        out_rows.append({
            "champion": res.name_a, "competitor": res.name_b,
            "mean_champ": res.mean_a, "mean_comp": res.mean_b,
            "mean_diff": res.mean_diff, "t": res.t_stat,
            "p_corrected": res.p_value, "df": res.df, "n": res.n,
            "significant_0.05": res.p_value < 0.05,
        })

    out = RESULTS_DIR / f"nadeau_bengio_{args.metric}.csv"
    pd.DataFrame(out_rows).to_csv(out, index=False)
    print(f"\nSaved → {out}")


if __name__ == "__main__":
    main()
