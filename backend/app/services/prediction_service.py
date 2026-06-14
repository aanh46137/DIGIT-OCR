"""
----------------------
High-level orchestration: takes raw image bytes, segments into lines,
runs TrOCR on each line, and returns structured predictions.
"""

from __future__ import annotations

import logging

import torch

from app.models.model_loader import (
    DEFAULT_BEAM_SIZE,
    DEFAULT_MAX_NEW_TOKENS,
    get_device,
    get_model,
    get_processor,
)
from app.schemas.prediction_response import PredictionResponse
from app.utils.digit_detection import detect_lines
from app.utils.image_processing import (
    binarize,
    bytes_to_grayscale,
    crop_to_pil_rgb,
)

logger = logging.getLogger(__name__)


def _predict_line_text(
    line_image,
    max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS,
    num_beams: int = DEFAULT_BEAM_SIZE,
) -> str:
    """Generates text from a single cropped line image using the TrOCR model."""
    processor = get_processor()
    model = get_model()
    device = get_device()

    pixel_values = processor(images=line_image, return_tensors="pt").pixel_values.to(device)

    with torch.no_grad():
        generated_ids = model.generate(
            pixel_values,
            max_new_tokens=max_new_tokens,
            num_beams=num_beams,
            early_stopping=True,
        )

    text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
    return text.strip()


def predict_multiline_image(
    image_bytes: bytes,
    filename: str,
    max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS,
    num_beams: int = DEFAULT_BEAM_SIZE,
) -> PredictionResponse:
    """
    Full pipeline:
      1. Decode image bytes -> grayscale
      2. Binarize -> detect line boundaries
      3. Crop each line, run TrOCR
      4. Join all lines with newlines

    Raises:
        ValueError: if the image can't be decoded or no lines are detected.
    """
    gray = bytes_to_grayscale(image_bytes)
    binary = binarize(gray)

    line_boxes = detect_lines(binary)
    if not line_boxes:
        raise ValueError("No text lines detected in the image.")

    line_texts: list[str] = []
    for i, box in enumerate(line_boxes, start=1):
        crop = crop_to_pil_rgb(gray, box.y_start, box.y_end)
        text = _predict_line_text(crop, max_new_tokens=max_new_tokens, num_beams=num_beams)
        line_texts.append(text)
        logger.info("Line %d/%d -> '%s'", i, len(line_boxes), text)

    # Join lines with real newlines
    prediction = "\n".join(line_texts)

    return PredictionResponse(
        filename=filename,
        prediction=prediction,
    )

