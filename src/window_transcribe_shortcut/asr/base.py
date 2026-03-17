from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str


@dataclass
class TranscriptResult:
    language: str
    segments: list[TranscriptSegment]


class ASRBackend:
    def transcribe(self, video_path: str, source_language: str | None = None) -> TranscriptResult:  # pragma: no cover - interface only
        raise NotImplementedError
