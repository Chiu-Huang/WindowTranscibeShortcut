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
