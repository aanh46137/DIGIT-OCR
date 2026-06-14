"""
-------------------
Line segmentation for multi-line digit-sequence images, using a horizontal
projection profile (sum of "ink" pixels per row). Splits an image into
per-line crops that can be fed individually to TrOCR.

If your handwriting is heavily skewed, consider replacing this with a
proper line-detection model (e.g. doctr's detection_predictor) — this
module exposes a simple `LineBox` interface so that swap is localized.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# ── Tunable defaults ──────────────────────────────────────────────────────────
MIN_LINE_HEIGHT = 15        # ignore bands shorter than this (pixels)
ROW_INK_THRESHOLD = 0.5     # fraction of max row-ink to count as "has text"
PADDING = 6                 # extra pixels above/below each cropped line


@dataclass(frozen=True)
class LineBox:
    """Represents one detected text line as a row range [y_start, y_end)."""
    y_start: int
    y_end: int

    @property
    def height(self) -> int:
        return self.y_end - self.y_start


def detect_lines(
    binary: np.ndarray,
    min_line_height: int = MIN_LINE_HEIGHT,
    row_ink_threshold: float = ROW_INK_THRESHOLD,
    padding: int = PADDING,
) -> list[LineBox]:
    """
    Given a binarized image (text=255, background=0), return a list of
    LineBox objects describing each detected text line, padded and
    clamped to the image bounds.
    """
    h, _ = binary.shape

    row_sums = binary.sum(axis=1).astype(np.float32)
    if row_sums.max() == 0:
        return []

    threshold = row_sums.max() * row_ink_threshold * 0.05
    has_text = row_sums > threshold

    bounds: list[tuple[int, int]] = []
    in_band = False
    start = 0

    for y, val in enumerate(has_text):
        if val and not in_band:
            start = y
            in_band = True
        elif not val and in_band:
            end = y
            if end - start >= min_line_height:
                bounds.append((start, end))
            in_band = False

    if in_band:
        end = len(has_text)
        if end - start >= min_line_height:
            bounds.append((start, end))

    # Apply padding, clamp to image bounds
    line_boxes = []
    for (y0, y1) in bounds:
        y0p = max(0, y0 - padding)
        y1p = min(h, y1 + padding)
        line_boxes.append(LineBox(y_start=y0p, y_end=y1p))

    return line_boxes

