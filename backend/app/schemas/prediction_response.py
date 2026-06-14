"""
prediction_response.py

Response schema for OCR prediction API.
"""

from pydantic import BaseModel, Field


class PredictionResponse(BaseModel):
    filename: str = Field(
        ...,
        description="Original uploaded filename"
    )
    prediction: str = Field(
        ...,
        description="Full recognized text with real newlines between lines"
    )


class ErrorResponse(BaseModel):
    detail: str