from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class WarmupRequest(BaseModel):
    source_lang: str | None = Field(default=None)


class TranscriptionRequest(BaseModel):
    video: Path = Field(description="Absolute or relative path to the local video file on the server machine.")
    source_lang: str | None = Field(default=None)


class SegmentResponse(BaseModel):
    start: float
    end: float
    text: str


class ModelInfoResponse(BaseModel):
    name: str
    device: str
    compute_type: str
    loaded_language: str | None = None


class TranscriptionResponse(BaseModel):
    detected_language: str
    segments: list[SegmentResponse]
    model: ModelInfoResponse
    processing_time_seconds: float


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model: ModelInfoResponse
