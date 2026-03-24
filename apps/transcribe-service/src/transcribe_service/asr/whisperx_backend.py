from __future__ import annotations

import time
from pathlib import Path
from threading import Lock
from typing import Any

from loguru import logger

from transcribe_service.asr.base import ASRBackend
from transcribe_service.models import ModelInfo, Segment, Transcript, TranscriptionResult


class WhisperXBackend(ASRBackend):
    def __init__(self, model_name: str, device: str, compute_type: str) -> None:
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self._model: Any | None = None
        self._loaded_language: str | None = None
        self._model_lock = Lock()

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def model_info(self) -> ModelInfo:
        return ModelInfo(
            name=self.model_name,
            device=self.device,
            compute_type=self.compute_type,
            loaded_language=self._loaded_language,
        )

    def preload(self, language: str | None = None) -> None:
        self._get_model(language=language)

    def transcribe(self, video_path: Path, language: str | None = None) -> TranscriptionResult:
        import whisperx

        resolved_video = video_path.expanduser().resolve()
        if not resolved_video.exists() or not resolved_video.is_file():
            raise FileNotFoundError(f"Video file not found: {resolved_video}")

        model = self._get_model(language=language)
        start = time.perf_counter()
        audio = whisperx.load_audio(str(resolved_video))
        payload = model.transcribe(audio, language=language)
        processing_time = time.perf_counter() - start

        detected_language = str(payload.get("language") or language or "").lower()
        segments = [
            Segment(
                start=float(segment.get("start", 0.0)),
                end=float(segment.get("end", 0.0)),
                text=str(segment.get("text", "")).strip(),
            )
            for segment in payload.get("segments", [])
            if isinstance(segment, dict)
        ]

        return TranscriptionResult(
            transcript=Transcript(language=detected_language, segments=segments),
            model_info=self.model_info,
            processing_time_seconds=processing_time,
        )

    def _get_model(self, language: str | None = None):
        with self._model_lock:
            should_reload = self._model is None or self._loaded_language != language
            if should_reload:
                import whisperx

                if self._model is None:
                    logger.info(
                        "Loading WhisperX model '{}' on {} ({})",
                        self.model_name,
                        self.device,
                        self.compute_type,
                    )
                else:
                    logger.info(
                        "Reloading WhisperX model '{}' for language {}",
                        self.model_name,
                        language or "auto",
                    )
                self._model = whisperx.load_model(
                    self.model_name,
                    self.device,
                    compute_type=self.compute_type,
                    language=language,
                )
                self._loaded_language = language

        if self._model is None:
            raise RuntimeError("Failed to load WhisperX model.")
        return self._model
