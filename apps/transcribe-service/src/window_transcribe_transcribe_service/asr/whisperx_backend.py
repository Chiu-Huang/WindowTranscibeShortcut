from __future__ import annotations

from pathlib import Path
from threading import Lock
from typing import Any

from loguru import logger

from window_transcribe_transcribe_service.asr.base import ASRBackend
from window_transcribe_transcribe_service.models import Segment, Transcript


class WhisperXBackend(ASRBackend):
    def __init__(self, model_name: str, device: str, compute_type: str) -> None:
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self._model: Any | None = None
        self._cached_language: str | None = None
        self._model_lock = Lock()

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def preload(self, language: str | None = None) -> None:
        self._get_model(language=language)

    def transcribe(self, video_path: Path, language: str | None = None) -> Transcript:
        import whisperx

        model = self._get_model(language=language)
        audio = whisperx.load_audio(str(video_path))
        result = model.transcribe(audio, language=language)

        detected = (result.get("language") or language or "").lower()
        segments = [
            Segment(
                start=float(seg.get("start", 0.0)),
                end=float(seg.get("end", 0.0)),
                text=str(seg.get("text", "")).strip(),
            )
            for seg in result.get("segments", [])
        ]
        return Transcript(language=detected, segments=segments)

    def _get_model(self, language: str | None = None):
        with self._model_lock:
            if self._model is None or self._cached_language != language:
                import whisperx

                if self._model is None:
                    logger.info("Loading WhisperX model '{}' on {}", self.model_name, self.device)
                else:
                    logger.info("Language mismatch: reloading WhisperX model for language {}", language)
                self._model = whisperx.load_model(
                    self.model_name,
                    self.device,
                    compute_type=self.compute_type,
                    language=language,
                )
                self._cached_language = language
        if self._model is None:
            raise RuntimeError("Failed to load WhisperX model for unknown reasons")
        return self._model
