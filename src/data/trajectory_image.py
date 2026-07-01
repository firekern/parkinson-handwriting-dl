"""
Static trajectory image rendering from PaHaW SVC files — PIL backend.

10 modalities: velocity, pressure, acceleration, effort, azimuth, altitude,
               rgb_vpa, rgb_vpe, rgb_vpz, raw

Output: (224, 224, 3) uint8 RGB — compatible with timm encoders.

Rendering is done entirely with PIL/NumPy (no matplotlib) for speed.
Plasma colormap is precomputed as a 256×3 uint8 lookup table.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from src.data.pahaw import N_TASKS, SVC_ROOT, read_svc

_IMG_SIZE = 224

# Plasma colormap lookup table (256 × 3 uint8) ------------------------------
def _build_plasma_lut() -> np.ndarray:
    import matplotlib.pyplot as plt
    cmap = plt.get_cmap("plasma")
    lut = (cmap(np.linspace(0, 1, 256))[:, :3] * 255).astype(np.uint8)
    import matplotlib
    matplotlib.pyplot.close("all")
    return lut

_PLASMA_LUT: np.ndarray = _build_plasma_lut()   # (256, 3) uint8


# Signal extraction ----------------------------------------------------------

def _signals(arr: np.ndarray) -> dict[str, np.ndarray]:
    x, y, t, btn = arr[:, 1], arr[:, 0], arr[:, 2], arr[:, 3]
    press, azimuth, altitude = arr[:, 6], arr[:, 4], arr[:, 5]
    dt = np.clip(np.diff(t), 1e-6, 100.0)
    vel = np.concatenate([[0.0], np.sqrt(np.diff(x) ** 2 + np.diff(y) ** 2) / dt])
    acc = np.concatenate([[0.0], np.abs(np.diff(vel)) / dt])
    dacc = np.diff(acc)
    jerk = np.concatenate([[0.0, 0.0], np.abs(dacc) / np.clip(dt[:len(dacc)], 1e-6, 100.0)])
    effort = vel * press
    return {
        "velocity": vel,
        "pressure": press,
        "acceleration": acc,
        "jerk": jerk[:len(x)],
        "effort": effort,
        "azimuth": azimuth,
        "altitude": altitude,
    }


# Normalisation ------------------------------------------------------------

def _norm_gamma(v: np.ndarray, gamma: float = 0.4) -> np.ndarray:
    """Percentile 2-98 clip → [0,1] → gamma correction."""
    lo, hi = np.percentile(v, 2), np.percentile(v, 98)
    if hi > lo:
        v = np.clip((v - lo) / (hi - lo), 0.0, 1.0)
    else:
        return np.zeros_like(v, dtype=np.float32)
    return np.power(v, gamma).astype(np.float32)


def _to_uint8_indices(v: np.ndarray) -> np.ndarray:
    """Float [0,1] → uint8 [0,255] for LUT lookup."""
    return np.clip(v * 255, 0, 255).astype(np.uint8)


# PIL rendering core --------------------------------------------------------

def _world_to_pixel(
    x: np.ndarray, y: np.ndarray,
    x_min: float, x_max: float,
    y_min: float, y_max: float,
    size: int,
    pad: int = 8,
) -> tuple[np.ndarray, np.ndarray]:
    """Map world coordinates to pixel coordinates with padding."""
    w = x_max - x_min or 1.0
    h = y_max - y_min or 1.0
    inner = size - 2 * pad
    px = ((x - x_min) / w * inner + pad).astype(np.int32)
    py = (size - pad - (y - y_min) / h * inner).astype(np.int32)  # flip Y
    return np.clip(px, 0, size - 1), np.clip(py, 0, size - 1)


def _render_mono(
    px: np.ndarray, py: np.ndarray,
    vals: np.ndarray,
    size: int = _IMG_SIZE,
) -> np.ndarray:
    """Draw coloured trajectory (plasma) on black canvas. Returns (H,W,3) uint8."""
    canvas = np.zeros((size, size, 3), dtype=np.uint8)
    if len(px) < 2:
        return canvas
    idx = _to_uint8_indices(_norm_gamma(vals))
    colors = _PLASMA_LUT[idx]          # (N, 3)
    # Draw each segment using Bresenham-style line in PIL
    img = Image.fromarray(canvas)
    draw = ImageDraw.Draw(img)
    for i in range(len(px) - 1):
        c = tuple(int(v) for v in colors[i])
        draw.line([(px[i], py[i]), (px[i + 1], py[i + 1])], fill=c, width=2)
    return np.array(img)


def _render_rgb(
    px: np.ndarray, py: np.ndarray,
    r_vals: np.ndarray, g_vals: np.ndarray, b_vals: np.ndarray,
    size: int = _IMG_SIZE,
) -> np.ndarray:
    """Draw RGB-encoded trajectory on black canvas."""
    canvas = np.zeros((size, size, 3), dtype=np.uint8)
    if len(px) < 2:
        return canvas
    r = _to_uint8_indices(_norm_gamma(r_vals))
    g = _to_uint8_indices(_norm_gamma(g_vals))
    b = _to_uint8_indices(_norm_gamma(b_vals))
    img = Image.fromarray(canvas)
    draw = ImageDraw.Draw(img)
    for i in range(len(px) - 1):
        draw.line([(px[i], py[i]), (px[i + 1], py[i + 1])],
                  fill=(int(r[i]), int(g[i]), int(b[i])), width=2)
    return np.array(img)


def _render_raw(
    px: np.ndarray, py: np.ndarray,
    size: int = _IMG_SIZE,
) -> np.ndarray:
    """White stroke on black canvas."""
    canvas = np.zeros((size, size, 3), dtype=np.uint8)
    if len(px) < 2:
        return canvas
    img = Image.fromarray(canvas)
    draw = ImageDraw.Draw(img)
    for i in range(len(px) - 1):
        draw.line([(px[i], py[i]), (px[i + 1], py[i + 1])], fill=(255, 255, 255), width=2)
    return np.array(img)


# Public API ------------------------------------------------------------

def svc_to_trajectory_image(
    path: Path,
    cfg,
    modality: str | None = None,
) -> np.ndarray:
    v = cfg.experiment.get("image", cfg.experiment.get("trajectory", {}))
    mod = modality if modality is not None else str(v.get("modality", "velocity"))

    if not path.exists():
        return np.zeros((_IMG_SIZE, _IMG_SIZE, 3), dtype=np.uint8)

    arr = read_svc(path)
    x, y, btn = arr[:, 1], arr[:, 0], arr[:, 3]
    on = btn == 1
    x_on, y_on = x[on], y[on]
    if len(x_on) < 2:
        return np.zeros((_IMG_SIZE, _IMG_SIZE, 3), dtype=np.uint8)

    pad_w = (x_on.max() - x_on.min()) * 0.05 or 1.0
    pad_h = (y_on.max() - y_on.min()) * 0.05 or 1.0
    px, py = _world_to_pixel(
        x_on, y_on,
        x_on.min() - pad_w, x_on.max() + pad_w,
        y_on.min() - pad_h, y_on.max() + pad_h,
        _IMG_SIZE,
    )

    if mod == "raw":
        return _render_raw(px, py)

    sigs = _signals(arr)

    if mod in ("rgb_vpa", "rgb_vpe", "rgb_vpz"):
        b_key = {"rgb_vpa": "acceleration", "rgb_vpe": "effort", "rgb_vpz": "azimuth"}[mod]
        return _render_rgb(px, py, sigs["velocity"][on], sigs["pressure"][on], sigs[b_key][on])

    if mod not in sigs:
        raise ValueError(f"Unknown modality '{mod}'")
    return _render_mono(px, py, sigs[mod][on])


def extract_subject_trajectory_images(
    subject_id: str,
    cfg,
    task: int | None = None,
    modality: str | None = None,
) -> list[np.ndarray]:
    tasks = [task] if task is not None else list(range(1, N_TASKS + 1))
    return [
        svc_to_trajectory_image(
            SVC_ROOT / subject_id / f"{subject_id}__{t}_1.svc", cfg, modality=modality
        )
        for t in tasks
    ]
