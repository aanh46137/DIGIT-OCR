# prediction.py - API OCR endpoint
"""
Prediction API routes.
------------------------
Exposes the /predict endpoint for multi-line digit-sequence OCR.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.models.model_loader import DEFAULT_MAX_NEW_TOKENS, DEFAULT_BEAM_SIZE
from app.schemas.prediction_response import ErrorResponse, PredictionResponse
from app.services.prediction_service import predict_multiline_image

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/predict", tags=["prediction"])

# Limit upload size to avoid abuse (e.g. 10 MB)
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/bmp", "image/tiff"}


@router.post(
    "",
    response_model=PredictionResponse,
    responses={400: {"model": ErrorResponse}, 415: {"model": ErrorResponse}},
    summary="Run multi-line digit OCR on an uploaded image",
)
async def predict(
    file: UploadFile = File(..., description="Image containing one or more rows of digits"),
    max_new_tokens: int = Query(DEFAULT_MAX_NEW_TOKENS, ge=1, le=256, description="Max tokens generated per line"),
    num_beams: int = Query(DEFAULT_BEAM_SIZE, ge=1, le=10, description="Beam search width"),
) -> PredictionResponse:
    """Handles HTTP requests for OCR prediction, processes the uploaded image, and returns the recognized text."""
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported content type '{file.content_type}'. "
                   f"Allowed: {sorted(ALLOWED_CONTENT_TYPES)}",
        )

    image_bytes = await file.read()

    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({len(image_bytes)} bytes). Max {MAX_UPLOAD_BYTES} bytes.",
        )

    try:
        result = predict_multiline_image(
            image_bytes=image_bytes,
            filename=file.filename or "uploaded_image",
            max_new_tokens=max_new_tokens,
            num_beams=num_beams,
        )
    except ValueError as e:
        logger.warning("Prediction failed for '%s': %s", file.filename, e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("Unexpected error during prediction for '%s'", file.filename)
        raise HTTPException(status_code=500, detail="Internal error during prediction.")

    return result


