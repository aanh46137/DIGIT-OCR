"""
model_loader.py
----------------
Loads the TrOCR model + processor once and exposes them as module-level
singletons so they aren't reloaded on every request.

Usage:
    from app.models.model_loader import get_model, get_processor, get_device
"""

import logging
from pathlib import Path

import torch
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────────────
MODEL_NAME = "microsoft/trocr-base-handwritten"

# Local path: backend/app/models/ -> backend/ -> DIGIT-OCR/ -> trained_models/trocr/
LOCAL_MODEL_DIR = Path(__file__).resolve().parents[3] / "trained_models" / "trocr"

# Generation params (override per-request if needed via prediction_service)
DEFAULT_MAX_NEW_TOKENS = 32 #64
DEFAULT_BEAM_SIZE = 1 #4

# ── Module-level singletons (lazy-loaded) ────────────────────────────────────
_processor: TrOCRProcessor | None = None
_model: VisionEncoderDecoderModel | None = None
_device: str | None = None


def _load() -> None:
    """
    Load model + processor into memory. Called once, on first access.

    Strategy:
      1. If trained_models/trocr/ exists locally → load from disk (fast, offline)
      2. Otherwise → download from Hugging Face, then save locally for next time
    """
    global _processor, _model, _device

    if _model is not None:
        return  # already loaded

    _device = "cuda" if torch.cuda.is_available() else "cpu"

    if LOCAL_MODEL_DIR.exists() and any(LOCAL_MODEL_DIR.iterdir()):
        # ── Load from local disk (fast) ──
        logger.info(
            "Loading TrOCR from local cache '%s' on %s ...",
            LOCAL_MODEL_DIR, _device
        )
        _processor = TrOCRProcessor.from_pretrained(str(LOCAL_MODEL_DIR))
        _model = VisionEncoderDecoderModel.from_pretrained(
            str(LOCAL_MODEL_DIR)
        ).to(_device)
    else:
        # ── Download from Hugging Face, then save locally ──
        logger.info(
            "Downloading TrOCR model '%s' on %s ...",
            MODEL_NAME, _device
        )
        _processor = TrOCRProcessor.from_pretrained(MODEL_NAME)
        _model = VisionEncoderDecoderModel.from_pretrained(
            MODEL_NAME
        ).to(_device)

        # Save to trained_models/trocr/ for next time
        LOCAL_MODEL_DIR.mkdir(parents=True, exist_ok=True)
        _processor.save_pretrained(str(LOCAL_MODEL_DIR))
        _model.save_pretrained(str(LOCAL_MODEL_DIR))
        logger.info(
            "Model saved to '%s' for future fast loading.",
            LOCAL_MODEL_DIR
        )

    _model.eval()
    logger.info("TrOCR model loaded successfully.")


def get_processor() -> TrOCRProcessor:
    """Returns the loaded TrOCR processor, initializing it if necessary."""
    _load()
    assert _processor is not None
    return _processor


def get_model() -> VisionEncoderDecoderModel:
    """Returns the loaded TrOCR model, initializing it if necessary."""
    _load()
    assert _model is not None
    return _model


def get_device() -> str:
    """Returns the computing device (CPU or CUDA) used by the model."""
    _load()
    assert _device is not None
    return _device


def warmup() -> None:
    """
    Call this from FastAPI's startup event so the (slow) first load happens
    when the server boots, not on the first incoming request.
    """
    _load()

