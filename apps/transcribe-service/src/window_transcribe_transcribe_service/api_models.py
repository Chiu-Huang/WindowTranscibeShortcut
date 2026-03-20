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


class TranscriptionResponse(BaseModel):
    detected_language: str
    subtitle_line_count: int
    segments: list[SegmentResponse]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_name: str
    device: str
