"""
Handcrafted clinical feature extraction from PaHaW SVC files.

33 features per task → mean + std across 8 tasks → 66-dim subject vector.

Feature index reference:
  Kinematic (on-surface):
     0  mean_vel            mean velocity (px/ms)
     1  std_vel             std velocity
     2  max_vel             max velocity
     3  vel_cv              coefficient of variation of velocity
     4  mean_acc            mean |acceleration|
     5  std_acc             std acceleration
     6  mean_jerk           mean |jerk| (smoothness — elevated in PD)
     7  std_jerk            std jerk
     8  mean_pressure       mean pen pressure
     9  std_pressure        std pen pressure
    10  max_pressure        max pen pressure
    11  press_cv            CV of pressure
    12  mean_press_diff     mean |dp/dt| (tremor in pressure signal)
  Temporal / structural:
    13  in_air_ratio        fraction of time with button=0
    14  n_strokes           number of on-surface strokes
    15  mean_stroke_dur     mean stroke duration (samples)
    16  std_stroke_dur      std stroke duration
    17  writing_time        total recording duration (s)
    18  mean_air_dur        mean in-air segment duration (samples)
  Path geometry:
    19  path_length         total on-surface path length (px)
    20  mean_curvature      mean angular change between segments (rad)
    21  n_dir_changes       zero-crossings of x-velocity
    22  bbox_ratio          bounding box width/height (micrographia proxy)
  Spectral (Welch PSD on velocity magnitude):
    23  tremor_power        PSD in 4–6 Hz tremor band
    24  lf_power            PSD in 0–2 Hz band
    25  hf_power            PSD in 8–12 Hz band
    26  dominant_freq       peak PSD frequency (Hz)
    27  spectral_entropy    Shannon entropy of normalised PSD
  Additional kinematic quality:
    28  mean_air_vel        mean velocity during in-air segments
    29  velocity_entropy    Shannon entropy of velocity histogram
    30  n_vel_peaks         local maxima count in velocity (tremor count)
    31  autocorr_vel        lag-1 autocorrelation of velocity
    32  tremor_power_press  PSD in 4–6 Hz on pressure signal
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from omegaconf import DictConfig
from scipy import signal as sp_signal

from src.data.pahaw import N_TASKS, read_svc, SVC_ROOT

N_FEAT_TASK = 33


def _safe_cv(arr: np.ndarray) -> float:
    m = arr.mean()
    return float(arr.std() / m) if abs(m) > 1e-6 else 0.0


def _stroke_stats(button: np.ndarray) -> tuple[int, float, float]:
    strokes, cur = [], None
    for b in button:
        if b == 1 and cur is None:
            cur = 0
        if b == 1 and cur is not None:
            cur += 1
        if b == 0 and cur is not None:
            strokes.append(cur)
            cur = None
    if cur is not None:
        strokes.append(cur)
    if not strokes:
        return 0, 0.0, 0.0
    a = np.array(strokes, dtype=np.float32)
    return len(strokes), float(a.mean()), float(a.std())


def _spectral(
    vel: np.ndarray,
    press: np.ndarray,
    fs: float,
    tremor_band: tuple[float, float],
    lf_band: tuple[float, float],
) -> tuple[float, float, float, float, float, float]:
    if len(vel) < 64:
        return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    nperseg = min(256, len(vel) // 2)
    freqs, psd = sp_signal.welch(vel, fs=fs, nperseg=nperseg)
    psd = np.maximum(psd, 1e-12)

    def _band(p: np.ndarray, lo: float, hi: float) -> float:
        mask = (freqs >= lo) & (freqs <= hi)
        return float(np.trapezoid(p[mask], freqs[mask])) if mask.any() else 0.0

    t_pow  = _band(psd, *tremor_band)
    lf_pow = _band(psd, *lf_band)
    hf_pow = _band(psd, 8.0, 12.0)
    dom_f  = float(freqs[np.argmax(psd)])
    norm   = psd / psd.sum()
    s_ent  = float(-(norm * np.log(norm + 1e-12)).sum())

    t_pow_press = 0.0
    if len(press) >= 64:
        fp, pp = sp_signal.welch(press, fs=fs, nperseg=min(256, len(press) // 2))
        pp = np.maximum(pp, 1e-12)
        mask_p = (fp >= tremor_band[0]) & (fp <= tremor_band[1])
        t_pow_press = float(np.trapezoid(pp[mask_p], fp[mask_p])) if mask_p.any() else 0.0

    return t_pow, lf_pow, hf_pow, dom_f, s_ent, t_pow_press


def _air_stats(
    btn: np.ndarray, x: np.ndarray, y: np.ndarray, t: np.ndarray
) -> tuple[float, float]:
    air = btn == 0
    if not air.any():
        return 0.0, 0.0
    durs: list[int] = []
    cur = 0
    for a in air:
        if a:
            cur += 1
        elif cur > 0:
            durs.append(cur)
            cur = 0
    if cur > 0:
        durs.append(cur)
    mean_air_dur = float(np.mean(durs)) if durs else 0.0

    dt = np.clip(np.diff(t), 1e-6, 100.0)
    dist = np.sqrt(np.diff(x) ** 2 + np.diff(y) ** 2)
    vel_all = dist / dt
    air_mask = air[1:]
    mean_air_vel = float(vel_all[air_mask].mean()) if air_mask.any() and vel_all[air_mask].size else 0.0
    return mean_air_dur, mean_air_vel


def _task_features(
    path: Path,
    fs: float,
    tremor_band: tuple[float, float],
    lf_band: tuple[float, float],
) -> np.ndarray:
    arr = read_svc(path)
    x, y, t, btn, press = arr[:, 1], arr[:, 0], arr[:, 2], arr[:, 3], arr[:, 6]

    dx, dy, dt = np.diff(x), np.diff(y), np.clip(np.diff(t), 1e-6, 100.0)
    vel = np.sqrt(dx ** 2 + dy ** 2) / dt
    vel_full = np.concatenate([[vel[0]], vel])

    acc  = np.abs(np.diff(vel) / dt[:-1]) if len(vel) > 1 else np.array([0.0])
    jerk = np.abs(np.diff(acc) / dt[:-2]) if len(acc) > 1 else np.array([0.0])

    on       = btn == 1
    vel_on   = vel_full[on] if on.any() else np.array([0.0])
    press_on = press[on]    if on.any() else np.array([0.0])

    mean_vel  = float(vel_on.mean())
    std_vel   = float(vel_on.std())
    max_vel   = float(vel_on.max())
    vel_cv    = _safe_cv(vel_on)
    mean_acc  = float(acc.mean())
    std_acc   = float(acc.std())
    mean_jerk = float(np.clip(jerk.mean(), 0, 1e6))
    std_jerk  = float(np.clip(jerk.std(),  0, 1e6))
    mean_press      = float(press_on.mean())
    std_press       = float(press_on.std())
    max_press       = float(press_on.max())
    press_cv        = _safe_cv(press_on)
    mean_press_diff = float(np.abs(np.diff(press_on)).mean()) if len(press_on) > 1 else 0.0

    in_air_ratio          = float((~on).sum()) / max(len(btn), 1)
    n_strk, m_dur, s_dur  = _stroke_stats(btn)
    writing_time          = float(np.clip(np.diff(t), 0, 100.0).sum()) / 1000.0 if len(t) > 1 else 0.0
    mean_air_dur, mean_air_vel = _air_stats(btn, x, y, t)

    x_on, y_on = x[on], y[on]
    if len(x_on) > 1:
        segs       = np.sqrt(np.diff(x_on) ** 2 + np.diff(y_on) ** 2)
        path_len   = float(segs.sum())
        angles     = np.arctan2(np.diff(y_on), np.diff(x_on))
        curv       = float(np.abs(np.diff(angles)).mean()) if len(angles) > 1 else 0.0
        w          = float(x_on.max() - x_on.min())
        h          = float(y_on.max() - y_on.min())
        bbox_ratio = w / (h + 1e-6)
    else:
        path_len = 0.0; curv = 0.0; bbox_ratio = 1.0

    vx_all = np.diff(x)
    n_dir_changes = int(((vx_all[:-1] * vx_all[1:]) < 0).sum()) if len(vx_all) > 1 else 0

    t_pow, lf_pow, hf_pow, dom_f, s_ent, t_pow_press = _spectral(
        vel_full, press_on, fs, tremor_band, lf_band
    )

    if len(vel_on) > 4:
        hist, _ = np.histogram(vel_on, bins=20, density=True)
        hist = np.maximum(hist, 1e-12); hist /= hist.sum()
        vel_entropy = float(-(hist * np.log(hist)).sum())
    else:
        vel_entropy = 0.0

    n_vel_peaks = int(
        ((vel_on[1:-1] > vel_on[:-2]) & (vel_on[1:-1] > vel_on[2:])).sum()
    ) if len(vel_on) > 2 else 0

    if len(vel_on) > 2:
        v = vel_on - vel_on.mean()
        autocorr = float(np.dot(v[:-1], v[1:]) / (np.dot(v, v) + 1e-12))
    else:
        autocorr = 0.0

    return np.array([
        mean_vel, std_vel, max_vel, vel_cv,
        mean_acc, std_acc,
        mean_jerk, std_jerk,
        mean_press, std_press, max_press, press_cv, mean_press_diff,
        in_air_ratio, float(n_strk), m_dur, s_dur, writing_time, mean_air_dur,
        path_len, curv, float(n_dir_changes), bbox_ratio,
        t_pow, lf_pow, hf_pow, dom_f, s_ent,
        mean_air_vel, vel_entropy, float(n_vel_peaks), autocorr, t_pow_press,
    ], dtype=np.float32)


def extract_subject_features(subject_id: str, cfg: DictConfig) -> np.ndarray:
    """Return 66-dim vector: mean + std of 33 features across all available tasks."""
    fs          = float(cfg.experiment.features.fs)
    tremor_band = tuple(cfg.experiment.features.tremor_band)
    lf_band     = tuple(cfg.experiment.features.lf_band)

    task_feats: list[np.ndarray] = []
    for task in range(1, N_TASKS + 1):
        p = SVC_ROOT / subject_id / f"{subject_id}__{task}_1.svc"
        task_feats.append(_task_features(p, fs, tremor_band, lf_band))

    mat = np.stack(task_feats)
    out = np.concatenate([mat.mean(0), mat.std(0)]).astype(np.float32)
    return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)


FEATURE_NAMES: list[str] = [
    f"{agg}_{name}"
    for agg in ("mean", "std")
    for name in (
        "mean_vel", "std_vel", "max_vel", "vel_cv",
        "mean_acc", "std_acc",
        "mean_jerk", "std_jerk",
        "mean_press", "std_press", "max_press", "press_cv", "mean_press_diff",
        "in_air_ratio", "n_strokes", "mean_stroke_dur", "std_stroke_dur",
        "writing_time", "mean_air_dur",
        "path_length", "curvature", "n_dir_changes", "bbox_ratio",
        "tremor_power", "lf_power", "hf_power", "dominant_freq", "spectral_entropy",
        "mean_air_vel", "velocity_entropy", "n_vel_peaks", "autocorr_vel",
        "tremor_power_press",
    )
]
