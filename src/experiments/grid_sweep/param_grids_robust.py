"""
Overfitting-resistant classifier registry for the *repeated* nested-CV sweep.

Differences vs. ``param_grids.HEAD_REGISTRY`` (the single-seed sweep):

* Grids are widened toward **stronger regularisation** (smaller ``C``, sparse
  ``l1``, shallow forests with larger leaves, MLP ``weight_decay``).
* Every head — including the two MLPs — has a **non-empty** grid, so the inner
  ``GridSearchCV`` actually tunes it and we can record the winning
  hyper-parameter per fold (the single-seed runner left the MLP grid empty and
  silently ran the default dropout).
* ``RandomForestClassifier`` runs with ``n_jobs=1`` so that the outer
  process-pool — not the estimator — owns the parallelism (no oversubscription).

All choices are documented inline; see ``STATISTICAL_ROBUSTNESS_REPORT.md``.
"""
from __future__ import annotations

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC

# Tunable hyper-parameter grid per head (anti-overfitting oriented). ------------
ROBUST_HEAD_REGISTRY: dict[str, dict] = {
    "logistic_regression": {
        "estimator": LogisticRegression(
            solver="liblinear", penalty="l2", max_iter=2000,
            class_weight="balanced", random_state=42,
        ),
        # liblinear (coordinate descent) is fast on small n and supports both
        # l1 and l2; l1 -> sparse weights; small C -> wide margin / shrinkage.
        "param_grid": {
            "penalty": ["l2", "l1"],
            "C": [0.01, 0.1, 1.0],
        },  # 6
    },
    "svm_linear": {
        "estimator": SVC(
            kernel="linear", probability=True,
            class_weight="balanced", random_state=42,
        ),
        # small C => larger margin => more robust on tiny cohorts.
        "param_grid": {"C": [0.003, 0.01, 0.1, 1.0]},  # 4
    },
    "svm_rbf": {
        "estimator": SVC(
            kernel="rbf", probability=True,
            class_weight="balanced", random_state=42,
        ),
        "param_grid": {
            "C": [0.1, 1.0, 10.0],
            "gamma": ["scale", "auto", 0.001],
        },  # 9
    },
    "svm_poly": {
        "estimator": SVC(
            kernel="poly", probability=True, gamma="scale",
            class_weight="balanced", random_state=42,
        ),
        "param_grid": {
            "C": [0.01, 0.1, 1.0],
            "degree": [2, 3],
        },  # 6
    },
    "random_forest": {
        "estimator": RandomForestClassifier(
            class_weight="balanced", max_features="sqrt",
            n_jobs=1, random_state=42,
        ),
        # few, shallow trees with large leaves => strong anti-overfit.
        "param_grid": {
            "n_estimators": [100, 200],
            "max_depth": [5, 10],
            "min_samples_leaf": [1, 3, 5],
        },  # 12
    },
    "mlp_small": {
        "estimator": None,  # lazy torch import in build_robust_estimator
        "param_grid": {
            "dropout": [0.3, 0.5],
            "weight_decay": [1e-3, 1e-2],
        },  # 4
    },
    "mlp_fixed": {
        "estimator": None,
        "param_grid": {
            "dropout": [0.3, 0.5],
            "weight_decay": [1e-3, 1e-2],
        },  # 4
    },
}


def build_robust_estimator(head_name: str, seed: int = 42):
    """Instantiate the base estimator for a head (lazy torch import for MLPs)."""
    if head_name == "mlp_fixed":
        from src.models.heads.mlp import FixedMLPClassifier
        return FixedMLPClassifier(seed=seed)
    if head_name == "mlp_small":
        from src.models.heads.mlp import SmallMLPClassifier
        return SmallMLPClassifier(seed=seed)
    from sklearn.base import clone
    return clone(ROBUST_HEAD_REGISTRY[head_name]["estimator"])
