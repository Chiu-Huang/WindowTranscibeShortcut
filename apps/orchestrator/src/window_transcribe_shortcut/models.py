from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Segment:
    start: float
    end: float
    text: str


@dataclass(slots=True)
class Transcript:
    language: str
    segments: list[Segment]


@dataclass(slots=True, frozen=True)
class JobResult:
    preset: str
    source_language: str
    target_language: str
    detected_language: str
    video: Path
    output: Path
    subtitle_line_count: int
    translation_applied: bool
    transcript: Transcript
