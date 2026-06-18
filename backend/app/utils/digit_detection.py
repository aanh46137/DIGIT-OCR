"""
-------------------
Line segmentation using Advanced OpenCV Contour Detection (Multi-layer Filtering).
Identifies character blobs, groups them vertically into rows, and applies
rigorous noise reduction (character-level and line-level density checks)
to eliminate hallucinations caused by margin artifacts or paper texture.
Excellent for dense, handwritten digit grids.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import cv2
import numpy as np

logger = logging.getLogger(__name__)

MIN_CONTOUR_AREA = 80       
MIN_CONTOUR_HEIGHT = 20    
MAX_CHAR_ASPECT_RATIO = 2.5 

PADDING = 6                 
ROW_TOLERANCE_RATIO = 0.6   
MIN_LINE_DENSITY = 0.02     


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
    padding: int = PADDING,
    min_area: int = MIN_CONTOUR_AREA,
    min_height: int = MIN_CONTOUR_HEIGHT,
) -> list[LineBox]:
    h_img, w_img = binary.shape

    # --- TẦNG 1: Xử lý và lọc Contour Character-level ---

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 3))
    dilated = cv2.dilate(binary, kernel, iterations=1)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        
        # 1.1 Lọc Diện tích
        if cv2.contourArea(cnt) < min_area:
            continue
            
        # 1.2 Lọc Chiều cao mảnh
        if h < min_height:
            continue
            
        # 1.3 Lọc Aspect Ratio (Chống vệt margin hoặc nét kẻ ngang)
        aspect_ratio = w / float(h)
        if aspect_ratio > MAX_CHAR_ASPECT_RATIO:
            continue
            
        boxes.append((x, y, w, h))

    if not boxes:
        logger.warning("No valid character contours found after character-level filtering.")
        return []

    boxes.sort(key=lambda b: b[1] + (b[3] / 2)) 

    lines = []
    current_line = [boxes[0]]

    for box in boxes[1:]:
        x, y, w, h = box
        cy = y + h / 2

        avg_cy = sum(b[1] + b[3] / 2 for b in current_line) / len(current_line)
        avg_h = sum(b[3] for b in current_line) / len(current_line)

        if abs(cy - avg_cy) < (avg_h * ROW_TOLERANCE_RATIO):
            current_line.append(box)
        else:
            lines.append(current_line)
            current_line = [box]

    if current_line:
        lines.append(current_line)

    line_boxes = []
    
    for i, line_chars in enumerate(lines, 1):
        # Xác định đỉnh và đáy thực tế của dòng
        y_min = min(b[1] for b in line_chars)
        y_max = max(b[1] + b[3] for b in line_chars)
        line_h = y_max - y_min
        
        # TẦNG 2: Lọc dòng quá mỏng 
        if line_h < min_height:
            logger.debug(f"Rejecting line {i}: height {line_h}px < {min_height}px.")
            continue

        y0_raw = max(0, int(y_min))
        y1_raw = min(h_img, int(y_max))
        
        if y1_raw <= y0_raw:
            continue
            
        roi_binary = binary[y0_raw:y1_raw, 0:w_img]
        
        # TẦNG 3: Kiểm tra mật độ (GIẢI PHÁP TRIỆT ĐỂ)
        num_black_pixels = np.sum(roi_binary == 255)
        total_roi_pixels = roi_binary.size if roi_binary.size > 0 else 1 
        
        density = num_black_pixels / float(total_roi_pixels)
        
        if density < MIN_LINE_DENSITY:
            logger.debug(f"Rejecting hallucinated line {i}: Density {density:.5f} < {MIN_LINE_DENSITY}.")
            continue 

        y0p = max(0, int(y_min - padding))
        y1p = min(h_img, int(y_max + padding))
        
        line_boxes.append(LineBox(y_start=y0p, y_end=y1p))

    line_boxes.sort(key=lambda lb: lb.y_start)
    
    logger.info(f"Detected {len(line_boxes)} valid lines after advanced multi-layer filtering.")

    return line_boxes