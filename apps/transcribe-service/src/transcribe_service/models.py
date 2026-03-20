from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Segment:
    start: float
    end: float
    text: str


@dataclass(slots=True)
class Transcript:
    language: str
    segments: list[Segment]


@dataclass(slots=True)
class ModelInfo:
    name: str
    device: str
    compute_type: str
    loaded_language: str | None


@dataclass(slots=True)
class TranscriptionResult:
    transcript: Transcript
    model_info: ModelInfo
    processing_time_seconds: float
