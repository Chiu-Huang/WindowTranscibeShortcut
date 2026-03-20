from __future__ import annotations

from pathlib import Path

from loguru import logger

from transcribe_service.asr import WhisperXBackend
from transcribe_service.config import settings
from transcribe_service.models import ModelInfo, TranscriptionResult


class TranscriptionService:
    def __init__(self) -> None:
        self.asr = WhisperXBackend(
            model_name=settings.whisper_model,
            device=settings.device,
            compute_type=settings.compute_type,
        )

    @property
    def is_model_loaded(self) -> bool:
        return self.asr.is_loaded

    @property
    def model_info(self) -> ModelInfo:
        return self.asr.model_info

    def preload_model(self, source_lang: str | None = None) -> None:
        logger.info("Preloading WhisperX model with source_lang={}", source_lang or "auto")
        self.asr.preload(language=source_lang)

    def transcribe(self, video_path: Path, source_lang: str | None) -> TranscriptionResult:
        logger.info("Starting transcription for {}", video_path)
        result = self.asr.transcribe(video_path, language=source_lang)
        logger.info("Detected language: {}", result.transcript.language or "unknown")
        logger.info("Generated {} transcript segments", len(result.transcript.segments))
        logger.info("Processing time: {:.3f}s", result.processing_time_seconds)
        return result
