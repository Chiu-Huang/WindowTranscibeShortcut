from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from window_transcribe_shortcut.presets import DEFAULT_PRESET


class TranscriptionRequest(BaseModel):
    video: Path = Field(description='Absolute or relative path to the local video file on the server machine.')
    preset: str = Field(default=DEFAULT_PRESET.name, description='Preset name to use for transcription.')
    output: Path | None = Field(default=None, description='Optional .srt output path on the server machine.')


class SegmentResponse(BaseModel):
    start: float
    end: float
    text: str


class TranscriptionResponse(BaseModel):
    preset: str
    source_language: str
    target_language: str
    detected_language: str
    video: Path
    output: Path
    subtitle_line_count: int
    segments: list[SegmentResponse]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_name: str
    device: str
    output_dir: Path
