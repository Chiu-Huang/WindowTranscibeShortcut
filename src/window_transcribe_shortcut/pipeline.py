from __future__ import annotations

from pathlib import Path

from loguru import logger

from window_transcribe_shortcut.asr import WhisperXBackend
from window_transcribe_shortcut.config import settings
from window_transcribe_shortcut.models import Segment, Transcript
from window_transcribe_shortcut.translators import (
    DeepLTranslator,
    GoogleWebTranslator,
    LibreTranslateTranslator,
    TranslationUnavailableError,
    Translator,
)
from window_transcribe_shortcut.utils import write_srt

CHINESE_LANGUAGE_CODES = {"zh", "zh-cn", "zh-tw"}


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

    def run(
        self,
        video_path: Path,
        output_path: Path,
        source_lang: str | None,
        target_lang: str,
    ) -> Transcript:
        logger.info("Starting transcription for {}", video_path)
        transcript = self.asr.transcribe(video_path, language=source_lang)
        logger.info("Detected language: {}", transcript.language or "unknown")
        logger.info("Generated {} transcript segments", len(transcript.segments))

        if self._should_translate(transcript.language, source_lang, target_lang):
            transcript = self._translate_transcript(
                transcript, source_lang=source_lang, target_lang=target_lang
            )

        write_srt(transcript, output_path)
        logger.info("Wrote subtitle file: {}", output_path)
        return transcript

    def _should_translate(
        self, detected_language: str | None, source_lang: str | None, target_lang: str
    ) -> bool:
        normalized_target = target_lang.lower()
        normalized_source = (detected_language or source_lang or "").lower()
        needs_translation = normalized_source not in CHINESE_LANGUAGE_CODES
        logger.debug(
            "Translation decision: target={}, source={}, translate={}",
            normalized_target,
            normalized_source or "unknown",
            normalized_target == "zh" and needs_translation,
        )
        return normalized_target == "zh" and needs_translation

    def _build_translators(self) -> list[Translator]:
        translators: dict[str, Translator] = {
            "deepl": DeepLTranslator(settings.deepl_api_key, settings.deepl_base_url),
            "google_web": GoogleWebTranslator(settings.google_translate_base_url),
            "libretranslate": LibreTranslateTranslator(
                settings.libretranslate_base_url,
                settings.libretranslate_api_key,
            ),
        }
        configured_services = [
            settings.translation_service,
            *settings.translation_fallback_services,
        ]
        ordered_services = list(dict.fromkeys(configured_services))
        return [translators[name] for name in ordered_services]

    def _translate_transcript(
        self, transcript: Transcript, source_lang: str | None, target_lang: str
    ) -> Transcript:
        source = source_lang or transcript.language or None
        lines = [segment.text for segment in transcript.segments]
        attempted_services: list[str] = []

        for translator in self._build_translators():
            attempted_services.append(translator.service_name)
            available, reason = translator.is_available()
            if not available:
                logger.warning(
                    "Skipping translation service '{}' because {}.",
                    translator.service_name,
                    reason or "it is unavailable",
                )
                continue

            logger.info(
                "Translating transcript to {} via {}",
                target_lang,
                translator.service_name,
            )
            try:
                translated_segments = translator.translate_lines(lines, source, target_lang)
            except TranslationUnavailableError as exc:
                logger.warning(
                    "Translation service '{}' became unavailable: {}",
                    translator.service_name,
                    exc,
                )
                continue
            except Exception as exc:  # pragma: no cover - network/service failure safety
                logger.warning(
                    "Translation via '{}' failed, trying next fallback if available: {}",
                    translator.service_name,
                    exc,
                )
                continue

            if len(translated_segments) != len(transcript.segments):
                logger.warning(
                    "Translation service '{}' returned {} lines for {} segments; skipping result.",
                    translator.service_name,
                    len(translated_segments),
                    len(transcript.segments),
                )
                continue

            logger.info(
                "Translated {} subtitle lines to {} via {}",
                len(translated_segments),
                target_lang,
                translator.service_name,
            )
            return Transcript(
                language=target_lang.lower(),
                segments=[
                    Segment(start=segment.start, end=segment.end, text=text)
                    for segment, text in zip(
                        transcript.segments, translated_segments, strict=True
                    )
                ],
            )

        logger.warning(
            "No translation service succeeded (attempted: {}). Keeping original transcript.",
            ", ".join(attempted_services) if attempted_services else "none",
        )
        return transcript


if __name__ == "__main__":
    print(settings.model_dump_json(indent=4))
