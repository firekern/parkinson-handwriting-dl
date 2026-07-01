"""
Classifier registry with HP grids for nested CV.

GridSearchCV scoring is always 'f1' (binary).
MLP has no grid — it is a fixed PyTorch model.
"""
from __future__ import annotations

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC

HEAD_REGISTRY: dict[str, dict] = {
    "logistic_regression": {
        "estimator": LogisticRegression(
            solver="saga", max_iter=2000, class_weight="balanced", random_state=42
        ),
        "param_grid": {
            "C": [0.01, 1.0, 100.0],          # 3 combo
        },
    },
    "svm_rbf": {
        "estimator": SVC(kernel="rbf", probability=True, class_weight="balanced", random_state=42),
        "param_grid": {
            "C": [0.1, 10.0, 100.0],
            "gamma": ["scale", "auto"],        # 6 combo
        },
    },
    "svm_linear": {
        "estimator": SVC(kernel="linear", probability=True, class_weight="balanced", random_state=42),
        "param_grid": {
            "C": [0.01, 1.0, 100.0],          # 3 combo
        },
    },
    "svm_poly": {
        "estimator": SVC(kernel="poly", probability=True, class_weight="balanced",
                         gamma="scale", random_state=42),
        "param_grid": {
            "C": [0.1, 10.0],
            "degree": [2, 3],                 # 4 combo
        },
    },
    "random_forest": {
        "estimator": RandomForestClassifier(
            class_weight="balanced", n_jobs=-1, random_state=42
        ),
        "param_grid": {
            "n_estimators": [200, 500],
            "max_depth": [None, 5, 10],        # 6 combo
        },
    },
    "mlp_fixed": {
        "estimator": None,
        "param_grid": {},                      # 1 combo — fixed
    },
    "mlp_small": {
        "estimator": None,
        "param_grid": {},                      # 64→32→2, dropout=0.3, fixed
    },
}


def build_estimator(head_name: str, seed: int = 42):
    """Instantiate the estimator for a given head (handles lazy imports)."""
    if head_name == "mlp_fixed":
        from src.models.heads.mlp import FixedMLPClassifier
        return FixedMLPClassifier(seed=seed)
    if head_name == "mlp_small":
        from src.models.heads.mlp import SmallMLPClassifier
        return SmallMLPClassifier(seed=seed)
    from sklearn.base import clone
    return clone(HEAD_REGISTRY[head_name]["estimator"])
