from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

EXCLUDED_SUBJECTS: frozenset[str] = frozenset({"00061", "00080", "00089"})

SVC_ROOT = Path(__file__).parents[2] / "data" / "raw" / "pahaw_extracted" / "PaHaW" / "PaHaW_public"
LABELS_CSV = Path(__file__).parents[2] / "data" / "processed" / "labels.csv"

N_TASKS = 8


def load_subjects(
    labels_csv: Path = LABELS_CSV,
) -> tuple[list[str], np.ndarray, np.ndarray]:
    """
    Load subject IDs, binary labels, and group indices from the labels CSV.

    Returns:
        subject_ids : list of str, length N
        y           : (N,) int64  —  1 = PD, 0 = HC
        groups      : (N,) int64  —  np.arange(N); one group per subject for
                      StratifiedGroupKFold (prevents subject-level data leakage)
    """
    df = pd.read_csv(labels_csv, dtype={"subject_id": str})
    df = df[~df["subject_id"].isin(EXCLUDED_SUBJECTS)].reset_index(drop=True)
    subject_ids = df["subject_id"].tolist()
    y = df["label"].values.astype(np.int64)
    groups = np.arange(len(subject_ids), dtype=np.int64)
    return subject_ids, y, groups


def read_svc(path: Path) -> np.ndarray:
    """
    Parse a PaHaW .svc file.

    Returns (N, 7) float32 array with columns:
        0: Y coordinate
        1: X coordinate
        2: timestamp (ms)
        3: button state (1 = on-surface, 0 = in-air)
        4: azimuth
        5: altitude
        6: pressure
    Returns a (2, 7) zero array when the file is missing or unreadable.
    """
    if not path.exists():
        return np.zeros((2, 7), dtype=np.float32)
    rows: list[list[float]] = []
    with open(path) as fh:
        fh.readline()
        for line in fh:
            parts = line.split()
            if len(parts) >= 7:
                rows.append([float(v) for v in parts[:7]])
    if not rows:
        return np.zeros((2, 7), dtype=np.float32)
    return np.array(rows, dtype=np.float32)


def task_path(subject_id: str, task: int) -> Path:
    """Return the .svc path for a given subject / task index (1-based)."""
    return SVC_ROOT / subject_id / f"{subject_id}__{task}_1.svc"
