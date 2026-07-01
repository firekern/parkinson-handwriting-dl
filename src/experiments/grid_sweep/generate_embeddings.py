"""
Generate per-task embeddings for the full experiment grid.

Pipeline (2 steps, rendering cached separately from encoding):

  Step 1 — Render once per modality:
    images: renders_img_{modality}.npy  → (72, 8, 224, 224, 3) uint8

  Step 2 — Encode per backbone (reuses cached renders):
    tasks_img_{backbone}_{modality}.npy → (72, 8, dim) float32
    tasks_handcrafted.npy               → (72, 8, 33) float32

Run:
    uv run python src/experiments/grid_sweep/generate_embeddings.py
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import torch
from tqdm import tqdm

from src.data.pahaw import N_TASKS, SVC_ROOT, load_subjects

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)

CACHE     = Path("data/processed")
RENDERS   = CACHE / "renders"

IMAGE_BACKBONES = [
    "swin_tiny_patch4_window7_224",
    "vit_base_patch16_224",
    "tf_efficientnet_b0",
]
MODALITIES = [
    "velocity", "acceleration", "altitude", "azimuth",
    "effort", "pressure",
    "rgb_vpa", "rgb_vpe", "rgb_vpz", "raw",
]

IMG_SIZE    = 224


def _auto_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


# Cache paths ------------------------------------------------------------

def img_render_path(modality: str)   -> Path: return RENDERS / f"renders_img_{modality}.npy"
def img_cache_path(backbone: str, modality: str) -> Path:
    return CACHE / f"tasks_img_{backbone}_{modality}.npy"
def hc_cache_path() -> Path: return CACHE / "tasks_handcrafted.npy"


# Step 1: Rendering ---------------------------------------------------------

def render_images(subject_ids: list[str], modality: str) -> np.ndarray:
    """Returns (N_subj, 8, 224, 224, 3) uint8."""
    from src.data.trajectory_image import svc_to_trajectory_image
    from omegaconf import OmegaConf

    cfg = OmegaConf.create({
        "experiment": {"image": {"color_gamma": 0.4, "modality": modality}}
    })
    n = len(subject_ids)
    X = np.zeros((n, N_TASKS, IMG_SIZE, IMG_SIZE, 3), dtype=np.uint8)
    for i, sid in enumerate(tqdm(subject_ids, desc=f"render img/{modality}", leave=False)):
        for t in range(1, N_TASKS + 1):
            p = SVC_ROOT / sid / f"{sid}__{t}_1.svc"
            X[i, t - 1] = svc_to_trajectory_image(p, cfg, modality=modality)
    return X


# Step 2: Encoding ----------------------------------------------------------

def encode_images(
    renders: np.ndarray,   # (N_subj, 8, H, W, 3) uint8
    backbone: str,
    device: torch.device,
) -> np.ndarray:
    """Returns (N_subj, 8, dim) float32."""
    from src.models.image.vit_encoder import build_vit_encoder, encode_image
    from PIL import Image as PILImage

    model, transform, dim = build_vit_encoder(backbone)
    model = model.to(device)

    n_subj, n_tasks = renders.shape[:2]
    X = np.zeros((n_subj, n_tasks, dim), dtype=np.float32)
    for i in range(n_subj):
        for t in range(n_tasks):
            img = PILImage.fromarray(renders[i, t])
            X[i, t] = encode_image(model, transform, img, device)
    return X


# Handcrafted ------------------------------------------------------------

def generate_handcrafted(subject_ids: list[str]) -> np.ndarray:
    """Returns (N_subj, 8, 33) float32."""
    from src.data.features import _task_features

    n = len(subject_ids)
    X = np.zeros((n, N_TASKS, 33), dtype=np.float32)
    for i, sid in enumerate(tqdm(subject_ids, desc="handcrafted", leave=False)):
        for t in range(1, N_TASKS + 1):
            p = SVC_ROOT / sid / f"{sid}__{t}_1.svc"
            feats = _task_features(p, fs=150.0, tremor_band=(4.0, 6.0), lf_band=(0.0, 2.0))
            X[i, t - 1] = np.nan_to_num(feats, nan=0.0, posinf=0.0, neginf=0.0)
    return X


# Main ------------------------------------------------------------

def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    subject_ids, _, _ = load_subjects()
    device = _auto_device()

    # Total jobs: 1 HC + 10 img_renders + 30 img_encodes = 41
    total_jobs = 1 + len(MODALITIES) + len(MODALITIES) * len(IMAGE_BACKBONES)
    done = 0

    def _step(label: str) -> None:
        nonlocal done
        done += 1
        pbar.set_description(f"[{done}/{total_jobs}] {label:<45}")
        pbar.update(1)

    log.info("Device: %s | Subjects: %d | Tasks: %d | Jobs: %d",
             device, len(subject_ids), N_TASKS, total_jobs)

    with tqdm(total=total_jobs, unit="job", ncols=100,
              bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:

        # Handcrafted ------------------------------------------------------
        path = hc_cache_path()
        if not path.exists():
            pbar.set_description(f"[{done+1}/{total_jobs}] handcrafted features")
            np.save(path, generate_handcrafted(subject_ids))
        _step("handcrafted ✓")

        # Images -----------------------------------------------------------
        for modality in MODALITIES:
            rpath = img_render_path(modality)
            if not rpath.exists():
                pbar.set_description(f"[{done+1}/{total_jobs}] render img/{modality}")
                renders = render_images(subject_ids, modality)
                np.save(rpath, renders)
            else:
                renders = None   # lazy load below if needed
            _step(f"render img/{modality} ✓")

            for backbone in IMAGE_BACKBONES:
                epath = img_cache_path(backbone, modality)
                if not epath.exists():
                    if renders is None:
                        renders = np.load(rpath)
                    pbar.set_description(f"[{done+1}/{total_jobs}] encode img/{backbone[:8]}/{modality}")
                    X = encode_images(renders, backbone, device)
                    np.save(epath, X)
                    renders = renders  # keep in memory for next backbone
                _step(f"encode img/{backbone[:8]}/{modality} ✓")

    log.info("All %d embeddings ready.", total_jobs)


if __name__ == "__main__":
    main()
