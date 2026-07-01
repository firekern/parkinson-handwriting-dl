"""
Complete pairwise significance analysis for the repeated nested-CV sweep.

Two questions the body of the paper only answers in part, here answered in full:

  (1) Champion vs *every* other representation (best head per input), not just the
      nearest eight: paired naive Student t-test AND the Nadeau-Bengio corrected
      resampled t-test on the same 30 folds, with full statistics.

  (2) The 7x7 classifier-head matrix: for each head we average F1 over the 31
      inputs within each of the 30 folds, then run the corrected paired test on
      every head pair (21 unordered pairs).

Outputs (CSV, consumed by the LaTeX tables and figures):
  results/all_heads_repeated/pairwise_champion_vs_all.csv
  results/all_heads_repeated/pairwise_heads_matrix_{t,p}.csv

Run:  uv run python -m src.analysis.full_pairwise
"""
from __future__ import annotations

from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from src.analysis.nadeau_bengio import (
    RESULTS_DIR, FOLD_KEY, load_cell, best_head_per_input,
    corrected_resampled_ttest,
)

METRIC = "test_f1"
HEADS = ["logistic_regression", "svm_linear", "svm_rbf", "svm_poly",
         "random_forest", "mlp_small", "mlp_fixed"]
HEAD_LABEL = {"logistic_regression": "LR", "svm_linear": "SVM-L",
              "svm_rbf": "SVM-R", "svm_poly": "SVM-P",
              "random_forest": "RF", "mlp_small": "MLP-s", "mlp_fixed": "MLP-f"}


def naive_paired_ttest(diffs: np.ndarray) -> tuple[float, float, int]:
    """Textbook paired t-test (assumes independent folds): t = d_bar / sqrt(s^2/N)."""
    d = np.asarray(diffs, float)
    n = d.size
    if d.var(ddof=1) == 0.0:
        return 0.0, 1.0, n - 1
    t = d.mean() / np.sqrt(d.var(ddof=1) / n)
    p = 2.0 * stats.t.sf(abs(t), n - 1)
    return float(t), float(p), n - 1


def _novid(df: pd.DataFrame) -> pd.DataFrame:
    return df[~df["input"].str.startswith("vid_")].reset_index(drop=True)


# --------------------------------------------------------------------------- #
# (1) champion vs every representation
# --------------------------------------------------------------------------- #
def champion_vs_all() -> pd.DataFrame:
    rank = _novid(best_head_per_input(METRIC))
    champ = rank.iloc[0]
    a = load_cell(champ["input"], champ["head"])
    rows = []
    for _, r in rank.iloc[1:].iterrows():
        b = load_cell(r["input"], r["head"])
        m = a.merge(b, on=FOLD_KEY, suffixes=("_a", "_b"))
        d = (m[f"{METRIC}_a"] - m[f"{METRIC}_b"]).to_numpy()
        tn, pn, _ = naive_paired_ttest(d)
        tc, pc, df = corrected_resampled_ttest(d)
        se = d.std(ddof=1) / np.sqrt(d.size)
        rows.append({
            "rank": len(rows) + 2,
            "input": r["input"], "head": r["head"],
            "mean_comp": r["mean"], "delta": d.mean(),
            "ci95_lo": d.mean() - 1.96 * se, "ci95_hi": d.mean() + 1.96 * se,
            "t_naive": tn, "p_naive": pn, "t_nb": tc, "p_nb": pc, "df": df,
            "sig_naive": pn < 0.05, "sig_nb": pc < 0.05,
        })
    out = pd.DataFrame(rows)
    out.attrs["champion"] = f"{champ['input']}/{champ['head']}"
    out.attrs["champ_mean"] = champ["mean"]
    return out


# --------------------------------------------------------------------------- #
# (2) head x head matrix (fold-averaged over inputs)
# --------------------------------------------------------------------------- #
def head_fold_means() -> pd.DataFrame:
    """Return a (30 folds x 7 heads) matrix of F1 averaged over the 31 inputs."""
    per_head = {}
    for h in HEADS:
        frames = []
        for f in RESULTS_DIR.glob(f"*__{h}.csv"):
            inp = f.stem.split("__", 1)[0]
            if inp.startswith("vid_"):
                continue
            df = pd.read_csv(f).sort_values(FOLD_KEY)
            frames.append(df.set_index(["seed", "outer_fold"])[METRIC].rename(inp))
        wide = pd.concat(frames, axis=1)
        per_head[h] = wide.mean(axis=1)
    return pd.DataFrame(per_head).sort_index()


def head_pairwise(folds: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, list]:
    labels = [HEAD_LABEL[h] for h in HEADS]
    T = pd.DataFrame(np.nan, index=labels, columns=labels)
    P = pd.DataFrame(np.nan, index=labels, columns=labels)
    rows = []
    for ha, hb in combinations(HEADS, 2):
        d = (folds[ha] - folds[hb]).to_numpy()
        tc, pc, df = corrected_resampled_ttest(d)
        tn, pn, _ = naive_paired_ttest(d)
        la, lb = HEAD_LABEL[ha], HEAD_LABEL[hb]
        T.loc[la, lb] = tc; T.loc[lb, la] = -tc
        P.loc[la, lb] = pc; P.loc[lb, la] = pc
        rows.append({"a": la, "b": lb, "delta": d.mean(),
                     "t_naive": tn, "p_naive": pn, "t_nb": tc, "p_nb": pc,
                     "sig_naive": pn < 0.05, "sig_nb": pc < 0.05})
    return T, P, rows


def main() -> None:
    cva = champion_vs_all()
    print(f"Champion: {cva.attrs['champion']}  F1={cva.attrs['champ_mean']:.3f}")
    print(f"  vs {len(cva)} representations:")
    print(f"  naive significant:     {int(cva['sig_naive'].sum()):2d}/{len(cva)}")
    print(f"  NB-corrected signif.:  {int(cva['sig_nb'].sum()):2d}/{len(cva)}")
    cva.to_csv(RESULTS_DIR / "pairwise_champion_vs_all.csv", index=False)

    folds = head_fold_means()
    T, P, rows = head_pairwise(folds)
    hp = pd.DataFrame(rows)
    print("\nHead pairwise (fold-averaged over 31 inputs), 21 pairs:")
    print(f"  naive significant:     {int(hp['sig_naive'].sum()):2d}/21")
    print(f"  NB-corrected signif.:  {int(hp['sig_nb'].sum()):2d}/21")
    T.to_csv(RESULTS_DIR / "pairwise_heads_matrix_t.csv")
    P.to_csv(RESULTS_DIR / "pairwise_heads_matrix_p.csv")
    hp.to_csv(RESULTS_DIR / "pairwise_heads_list.csv", index=False)
    print("\nSaved 4 CSVs ->", RESULTS_DIR)
    # echo the champion-vs-all table for the appendix
    show = cva[["rank", "input", "head", "delta", "p_naive", "p_nb",
                "sig_naive", "sig_nb"]].copy()
    with pd.option_context("display.max_rows", None, "display.width", 200):
        print("\n", show.to_string(index=False))


if __name__ == "__main__":
    main()
