from __future__ import annotations

from pathlib import Path

from loguru import logger

from window_transcribe_shortcut.clients import (
    TranscribeServiceClient,
    TranslationServiceClient,
)
from window_transcribe_shortcut.config import settings
from window_transcribe_shortcut.models import JobResult, Segment, Transcript
from window_transcribe_shortcut.presets import Preset
from window_transcribe_shortcut.utils import ensure_video_file, write_srt

CHINESE_LANGUAGE_CODES = {"zh", "zh-cn", "zh-tw"}


class TranscriptionService:
    def __init__(self) -> None:
        self.transcribe_client = TranscribeServiceClient(
            settings.transcribe_service_url,
            timeout_seconds=settings.service_request_timeout_seconds,
        )
        self.translation_client = TranslationServiceClient(
            settings.translation_service_url,
            timeout_seconds=settings.service_request_timeout_seconds,
        )

    @property
    def is_model_loaded(self) -> bool:
        health = self.transcribe_client.health()
        return bool(health.get("model_loaded"))

    def preload_model(self, source_lang: str | None = None) -> None:
        self.transcribe_client.preload(source_lang=source_lang)

    def run(self, video_path: Path, output_path: Path, preset: Preset) -> JobResult:
        resolved_video = ensure_video_file(video_path)
        logger.info("Starting orchestrated subtitle job for {}", resolved_video)

        transcript = self.transcribe_client.transcribe(
            resolved_video,
            source_lang=preset.source_lang,
        )
        detected_language = transcript.language or preset.source_lang or "unknown"
        logger.info("Detected language: {}", detected_language)
        logger.info("Generated {} transcript segments", len(transcript.segments))

        translation_applied = self._should_translate(
            detected_language=detected_language,
            preset=preset,
        )
        if translation_applied:
            transcript = self._translate_transcript(
                transcript,
                source_lang=preset.source_lang,
                target_lang=preset.target_lang,
            )

        write_srt(transcript, output_path)
        logger.info("Wrote subtitle file: {}", output_path)

        return JobResult(
            preset=preset.name,
            source_language=preset.source_lang or "auto",
            target_language=preset.target_lang,
            detected_language=detected_language,
            video=resolved_video,
            output=output_path,
            subtitle_line_count=len(transcript.segments),
            translation_applied=translation_applied,
            transcript=transcript,
        )

    def _should_translate(self, detected_language: str | None, preset: Preset) -> bool:
        normalized_target = preset.target_lang.lower()
        normalized_detected = (detected_language or preset.source_lang or "").lower()
        needs_translation = normalized_detected not in CHINESE_LANGUAGE_CODES
        should_translate = normalized_target == "zh" and needs_translation
        logger.debug(
            "Translation decision: preset={}, target={}, detected={}, translate={}",
            preset.name,
            normalized_target,
            normalized_detected or "unknown",
            should_translate,
        )
        return should_translate

    def _translate_transcript(
        self,
        transcript: Transcript,
        source_lang: str | None,
        target_lang: str,
    ) -> Transcript:
        source = source_lang or transcript.language or None
        translated_segments = self.translation_client.translate_segments(
            transcript.segments,
            source_lang=source,
            target_lang=target_lang,
        )

        if len(translated_segments) != len(transcript.segments):
            raise RuntimeError(
                "Translation service returned a different number of lines "
                f"({len(translated_segments)}) than the transcript ({len(transcript.segments)})."
            )

        logger.info("Translated {} subtitle lines to {}", len(translated_segments), target_lang)
        return Transcript(
            language=target_lang.lower(),
            segments=translated_segments,
        )
