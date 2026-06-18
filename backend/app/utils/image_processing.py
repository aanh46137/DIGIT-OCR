"""
--------------------
Low-level image utilities: decoding uploaded bytes, resizing, binarization,
margin clearing, and saving intermediate results for debugging.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


def bytes_to_grayscale(image_bytes: bytes, target_width: int = 1024) -> np.ndarray:
    """
    Decode raw image bytes (e.g. from an UploadFile) into a grayscale
    numpy array (H, W), uint8, and resize it to a standard width.
    """
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    gray = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)

    if gray is None:
        raise ValueError("Could not decode image bytes — unsupported or corrupt image.")

    h, w = gray.shape
    if w != target_width:
        ratio = target_width / w
        new_h = int(h * ratio)
        gray = cv2.resize(gray, (target_width, new_h), interpolation=cv2.INTER_AREA)

    return gray


def binarize(gray: np.ndarray) -> np.ndarray:
    """
    Adaptive binarization + XÓA VIỀN ẢNH + KHỬ BÓNG ĐỔ
    Returns a binary image where text/ink pixels = 255, background = 0.
    """
    binary = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        51, 
        25  
    )
    
    h, w = binary.shape
    border_y = 25
    border_x = 5
    binary[0:border_y, :] = 0          
    binary[h-border_y:h, :] = 0        
    binary[:, 0:border_x] = 0         
    binary[:, w-border_x:w] = 0        
    
    return binary


def gray_to_pil_rgb(gray: np.ndarray) -> Image.Image:
    """Convert a grayscale numpy array to a PIL RGB image (TrOCR expects RGB)."""
    rgb = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
    return Image.fromarray(rgb)


def crop_to_pil_rgb(gray_full: np.ndarray, y0: int, y1: int) -> Image.Image:
    """Crop rows [y0:y1] from a grayscale image and return as PIL RGB."""
    crop = gray_full[y0:y1, :]
    return gray_to_pil_rgb(crop)


def save_debug_image(image: Image.Image, output_dir: str | Path, prefix: str = "debug") -> Path:
    """
    Save an intermediate image (e.g. binarized or annotated) to
    `uploads/results/` for debugging/inspection.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{prefix}_{uuid.uuid4().hex[:8]}.png"
    out_path = output_dir / filename
    image.save(out_path)

    logger.debug("Saved debug image to %s", out_path)
    return out_path