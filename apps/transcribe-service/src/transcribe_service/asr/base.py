from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from transcribe_service.models import TranscriptionResult


class ASRBackend(ABC):
    @abstractmethod
    def preload(self, language: str | None = None) -> None:
        raise NotImplementedError

    @property
    @abstractmethod
    def is_loaded(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def transcribe(self, video_path: Path, language: str | None = None) -> TranscriptionResult:
        raise NotImplementedError
