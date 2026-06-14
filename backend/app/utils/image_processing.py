"""
--------------------
Low-level image utilities: decoding uploaded bytes, binarization,
and saving intermediate results for debugging.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


def bytes_to_grayscale(image_bytes: bytes) -> np.ndarray:
    """
    Decode raw image bytes (e.g. from an UploadFile) into a grayscale
    numpy array (H, W), uint8.
    """
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    gray = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)

    if gray is None:
        raise ValueError("Could not decode image bytes — unsupported or corrupt image.")

    return gray


def binarize(gray: np.ndarray) -> np.ndarray:
    """
    Otsu binarization: returns a binary image where text/ink pixels = 255,
    background = 0. Useful for line-segmentation projection profiles.
    """
    _, binary = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )
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



# # image_processing.py - Resize, Gray, Threshold...
# # TODO: Implement image preprocessing functions
# """
# Image preprocessing utilities for Digit OCR.
# """

# from pathlib import Path

# import cv2
# import numpy as np


# def read_image(image_path: str | Path) -> np.ndarray:
#     """
#     Read image from disk.

#     Args:
#         image_path: Path to image.

#     Returns:
#         np.ndarray: Original image.
#     """

#     image = cv2.imread(str(image_path))

#     if image is None:
#         raise FileNotFoundError(
#             f"Cannot read image: {image_path}"
#         )

#     return image


# def convert_to_grayscale(image: np.ndarray) -> np.ndarray:
#     """
#     Convert BGR image to grayscale.

#     Args:
#         image: Original image.

#     Returns:
#         np.ndarray: Grayscale image.
#     """

#     return cv2.cvtColor(
#         image,
#         cv2.COLOR_BGR2GRAY
#     )

# def apply_gaussian_blur(
#     image: np.ndarray,
#     kernel_size: tuple[int, int] = (3, 3)
# ) -> np.ndarray:
#     """
#     Reduce image noise.

#     Args:
#         image: Grayscale image.
#         kernel_size: Gaussian kernel size.

#     Returns:
#         np.ndarray: Blurred image.
#     """

#     return cv2.GaussianBlur(
#         image,
#         kernel_size,
#         0
#     )


# # def resize_image(
# #     image: np.ndarray,
# #     width: int = 28,
# #     height: int = 28
# # ) -> np.ndarray:
# #     """
# #     Resize image.

# #     Args:
# #         image: Input image.
# #         width: Target width.
# #         height: Target height.

# #     Returns:
# #         np.ndarray: Resized image.
# #     """

# #     return cv2.resize(
# #         image,
# #         (width, height)
# #     )


# def apply_threshold(
#     image: np.ndarray
# ) -> np.ndarray:
#     """
#     Convert grayscale image to binary image.

#     Args:
#         image: Grayscale image.

#     Returns:
#         np.ndarray: Binary image.
#     """

#     # Dùng Adaptive Threshold tốt hơn cho ảnh chụp giấy có ánh sáng bóng đổ
#     threshold_image = cv2.adaptiveThreshold(
#         image,
#         255,
#         cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
#         cv2.THRESH_BINARY_INV,
#         31, # Block size (nên là số lẻ, lớn hơn để bắt nét chữ to)
#         15  # C (hằng số trừ đi để giảm nhiễu)
#     )

#     return threshold_image


# # def normalize_image(
# #     image: np.ndarray
# # ) -> np.ndarray:
# #     """
# #     Normalize pixel values to [0, 1].

# #     Args:
# #         image: Input image.

# #     Returns:
# #         np.ndarray: Normalized image.
# #     """

# #     return image.astype("float32") / 255.0

# def save_image(
#     image: np.ndarray,
#     output_path: str | Path
# ) -> None:
#     """
#     Save image to disk.

#     Args:
#         image: Image array.
#         output_path: Output image path.
#     """
#     output_path = Path(output_path)

#     output_path.parent.mkdir(
#         parents=True,
#         exist_ok=True
#     )

#     cv2.imwrite(
#         str(output_path),
#         image
#     )