"""
PyTorch MLP heads — sklearn-compatible interfaces.

FixedMLPClassifier : input_dim → 128 → 64 → 2, dropout=0.5
SmallMLPClassifier : input_dim →  64 → 32 → 2, dropout=0.3
Optimiser: AdamW  lr=1e-3  weight_decay=1e-3  |  200 epochs full-batch
"""
from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.preprocessing import LabelEncoder


class _MLP(nn.Module):
    def __init__(self, input_dim: int, dropout: float = 0.5) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(128, 64),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(64, 2),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class FixedMLPClassifier(BaseEstimator, ClassifierMixin):
    """sklearn-compatible wrapper for the PyTorch MLP.

    ``dropout`` is exposed as a constructor param so GridSearchCV can tune it
    on the validation folds (grid {0.1, 0.2, 0.5}).
    """

    def __init__(self, seed: int = 42, dropout: float = 0.5,
                 weight_decay: float = 1e-3) -> None:
        self.seed = seed
        self.dropout = dropout
        self.weight_decay = weight_decay

    def fit(self, X: np.ndarray, y: np.ndarray) -> "FixedMLPClassifier":
        torch.manual_seed(self.seed)
        np.random.seed(self.seed)

        self.classes_ = np.unique(y)
        self.le_ = LabelEncoder().fit(y)
        y_enc = self.le_.transform(y)

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_ = _MLP(X.shape[1], dropout=self.dropout).to(device)

        X_t = torch.tensor(X, dtype=torch.float32).to(device)
        y_t = torch.tensor(y_enc, dtype=torch.long).to(device)

        # class weights for imbalance
        counts = np.bincount(y_enc)
        weights = torch.tensor(1.0 / counts, dtype=torch.float32).to(device)
        criterion = nn.CrossEntropyLoss(weight=weights)
        optimiser = torch.optim.AdamW(self.model_.parameters(), lr=1e-3,
                                      weight_decay=self.weight_decay)

        self.model_.train()
        for _ in range(200):
            optimiser.zero_grad()
            criterion(self.model_(X_t), y_t).backward()
            optimiser.step()

        self.model_.eval()
        self._device = device
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        X_t = torch.tensor(X, dtype=torch.float32).to(self._device)
        with torch.no_grad():
            logits = self.model_(X_t)
            probs = torch.softmax(logits, dim=1).cpu().numpy()
        return probs

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.classes_[np.argmax(self.predict_proba(X), axis=1)]


class _SmallMLP(nn.Module):
    def __init__(self, input_dim: int, dropout: float = 0.3) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(64, 32),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(32, 2),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class SmallMLPClassifier(BaseEstimator, ClassifierMixin):
    """64 → 32 → 2, dropout=0.3. sklearn-compatible.

    Supports mini-batch training via batch_size (full-batch when N <= batch_size).
    Deterministic: seeded Generator for DataLoader shuffling.
    """

    def __init__(self, seed: int = 42, dropout: float = 0.3,
                 n_epochs: int = 200, batch_size: int = 512,
                 weight_decay: float = 1e-3) -> None:
        self.seed = seed
        self.dropout = dropout
        self.n_epochs = n_epochs
        self.batch_size = batch_size
        self.weight_decay = weight_decay

    def fit(self, X: np.ndarray, y: np.ndarray) -> "SmallMLPClassifier":
        import torch.utils.data as D

        torch.manual_seed(self.seed)
        np.random.seed(self.seed)

        self.classes_ = np.unique(y)
        self.le_ = LabelEncoder().fit(y)
        y_enc = self.le_.transform(y)

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_ = _SmallMLP(X.shape[1], dropout=self.dropout).to(device)

        X_t = torch.tensor(X, dtype=torch.float32)
        y_t = torch.tensor(y_enc, dtype=torch.long)

        counts = np.bincount(y_enc)
        weights = torch.tensor(1.0 / counts, dtype=torch.float32).to(device)
        criterion = nn.CrossEntropyLoss(weight=weights)
        optimiser = torch.optim.AdamW(self.model_.parameters(), lr=1e-3,
                                      weight_decay=self.weight_decay)

        bs = min(self.batch_size, len(X_t))
        loader = D.DataLoader(
            D.TensorDataset(X_t, y_t),
            batch_size=bs,
            shuffle=True,
            generator=torch.Generator().manual_seed(self.seed),
        )

        self.model_.train()
        for _ in range(self.n_epochs):
            for X_b, y_b in loader:
                X_b, y_b = X_b.to(device), y_b.to(device)
                optimiser.zero_grad()
                criterion(self.model_(X_b), y_b).backward()
                optimiser.step()

        self.model_.eval()
        self._device = device
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        X_t = torch.tensor(X, dtype=torch.float32).to(self._device)
        with torch.no_grad():
            logits = self.model_(X_t)
            probs = torch.softmax(logits, dim=1).cpu().numpy()
        return probs

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.classes_[np.argmax(self.predict_proba(X), axis=1)]
