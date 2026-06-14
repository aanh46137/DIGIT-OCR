"""
Main entry point for Digit OCR FastAPI application.
-------
FastAPI application entrypoint.

Key additions for TrOCR integration:
  - Warm up the TrOCR model on startup (avoids slow first request)
  - Include the prediction router
  - CORS for the Vite frontend
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models.model_loader import warmup
from app.routers import prediction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Digit OCR API",
    description="Multi-line handwritten digit sequence recognition using TrOCR",
    version="1.0.0",
)

# ── CORS — adjust origins for your deployed frontend ──────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production, e.g. ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(prediction.router)


@app.on_event("startup")
async def on_startup() -> None:
    """Load the TrOCR model into memory before serving requests."""
    logger.info("Starting up — warming up TrOCR model ...")
    warmup()
    logger.info("Startup complete.")


@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok"}



# from fastapi import FastAPI

# from app.routers.prediction import router as prediction_router


# app = FastAPI(
#     title="Digit OCR API",
#     description="API for recognizing single and multiple digits from images.",
#     version="1.0.0",
# )

# # Register routers
# app.include_router(
#     prediction_router,
#     prefix="/api/v1",
#     tags=["Prediction"],
# )


# @app.get("/")
# async def root() -> dict:
#     """
#     Root endpoint.

#     Returns:
#         dict: Welcome message.
#     """
#     return {
#         "message": "Digit OCR API is running."
#     }

