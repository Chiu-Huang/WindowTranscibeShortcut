from __future__ import annotations

from pathlib import Path

from loguru import logger

from window_transcribe_transcribe_service.asr import WhisperXBackend
from window_transcribe_transcribe_service.config import settings
from window_transcribe_transcribe_service.models import Transcript


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

    def preload_model(self, source_lang: str | None = None) -> None:
        self.asr.preload(language=source_lang)

    def transcribe(self, video_path: Path, source_lang: str | None) -> Transcript:
        logger.info("Starting transcription for {}", video_path)
        transcript = self.asr.transcribe(video_path, language=source_lang)
        logger.info("Detected language: {}", transcript.language or "unknown")
        logger.info("Generated {} transcript segments", len(transcript.segments))
        return transcript
