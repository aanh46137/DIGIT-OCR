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
from app.utils.text_postprocess import sanitize_line

logger = logging.getLogger(__name__)

# Số lượng ảnh xử lý đồng thời (Chống tràn RAM, nếu GPU mạnh có thể tăng lên 16)
BATCH_SIZE = 8 

def _predict_batch_text(
    line_images: list,
    max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS,
    num_beams: int = DEFAULT_BEAM_SIZE,
) -> list[str]:
    """CẬP NHẬT: Xử lý nhiều hình ảnh CÙNG LÚC thay vì từng ảnh một -> Tăng tốc độ cực lớn"""
    if not line_images:
        return []

    processor = get_processor()
    model = get_model()
    device = get_device()

    # Nạp toàn bộ lô ảnh vào processor
    pixel_values = processor(images=line_images, return_tensors="pt").pixel_values.to(device)

    with torch.no_grad():
        generated_ids = model.generate(
            pixel_values,
            max_new_tokens=max_new_tokens,
            num_beams=num_beams,
            early_stopping=True,
        )

    # Decode toàn bộ kết quả một lần
    raw_texts = processor.batch_decode(generated_ids, skip_special_tokens=True)
    return raw_texts


def predict_multiline_image(
    image_bytes: bytes,
    filename: str,
    max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS,
    num_beams: int = DEFAULT_BEAM_SIZE,
) -> PredictionResponse:
    
    gray = bytes_to_grayscale(image_bytes, target_width=1024)
    binary = binarize(gray)

    line_boxes = detect_lines(binary)
    if not line_boxes:
        raise ValueError("No text lines detected in the image.")

    # 1. Cắt toàn bộ hình ảnh và lưu vào danh sách
    crops = [crop_to_pil_rgb(gray, box.y_start, box.y_end) for box in line_boxes]
    
    line_texts: list[str] = []
    
    # 2. Xử lý song song theo từng Lô (Batch)
    for i in range(0, len(crops), BATCH_SIZE):
        batch_crops = crops[i:i + BATCH_SIZE]
        raw_texts = _predict_batch_text(batch_crops, max_new_tokens, num_beams)
        
        for raw_text in raw_texts:
            # Dọn dẹp: TUYỆT ĐỐI CHỈ LẤY SỐ
            cleaned = sanitize_line(raw_text)
            if cleaned:
                line_texts.append(cleaned)
                
    if not line_texts:
         raise ValueError("No valid numbers could be extracted from the image.")

    prediction = "\n".join(line_texts)

    return PredictionResponse(
        filename=filename,
        prediction=prediction,
    )