"""
Frozen ViT / Swin image encoders via timm.

Supported backbones (any timm model with num_classes=0 support):
  swin_tiny_patch4_window7_224  — Swin-T, ImageNet-1k, 768-dim
  swinv2_tiny_window8_256       — Swin-V2-T, ImageNet,  768-dim
  vit_base_patch16_224          — ViT-B/16, ImageNet-21k, 768-dim
  vit_small_patch16_224         — ViT-S/16, ImageNet-1k,  384-dim
  deit_small_patch16_224        — DeiT-S,   ImageNet-1k,  384-dim
  efficientnet_b0               — EfficientNet-B0, 1280-dim

Usage:
    model, transform, embed_dim = build_vit_encoder(backbone_name)
    emb = encode_image(model, transform, pil_image_or_uint8_array, device)
"""
from __future__ import annotations

from typing import Callable

import numpy as np
import timm
import timm.data
import torch
import torch.nn as nn
from PIL import Image


def build_vit_encoder(backbone: str) -> tuple[nn.Module, Callable, int]:
    """Load a frozen timm encoder. Returns (model, transform, embed_dim)."""
    model = timm.create_model(backbone, pretrained=True, num_classes=0)
    model.eval()
    for p in model.parameters():
        p.requires_grad_(False)

    data_cfg = timm.data.resolve_model_data_config(model)
    transform = timm.data.create_transform(**data_cfg, is_training=False)
    embed_dim = model.num_features

    return model, transform, embed_dim


@torch.no_grad()
def encode_image(
    model: nn.Module,
    transform: Callable,
    image: np.ndarray | Image.Image,
    device: torch.device,
) -> np.ndarray:
    """
    Encode a single image.

    Args:
        image: (H, W, 3) uint8 ndarray or PIL Image.

    Returns:
        (embed_dim,) float32 embedding.
    """
    if isinstance(image, np.ndarray):
        image = Image.fromarray(image)
    x = transform(image).unsqueeze(0).to(device)
    return model(x).squeeze(0).cpu().numpy()
