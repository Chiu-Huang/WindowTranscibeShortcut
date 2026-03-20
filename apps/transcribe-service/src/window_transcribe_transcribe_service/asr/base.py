from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from window_transcribe_transcribe_service.models import Transcript


class ASRBackend(ABC):
    @abstractmethod
    def transcribe(self, video_path: Path, language: str | None = None) -> Transcript:
        raise NotImplementedError
