from __future__ import annotations

from dataclasses import asdict

from window_transcribe_translation_service.api_models import SubtitleSegment
from window_transcribe_translation_service.config import settings
from window_transcribe_translation_service.providers import ProviderRouter, TranslationAttempt


class TranslationService:
    def __init__(self) -> None:
        self.router = ProviderRouter.from_settings(settings)

    def health_summary(self) -> tuple[list[str], list[dict[str, object]]]:
        providers = [asdict(descriptor) for descriptor in self.router.list_providers()]
        return settings.translation_provider_order, providers

    def list_providers(self) -> list[dict[str, object]]:
        return [asdict(descriptor) for descriptor in self.router.list_providers()]

    def translate_lines(
        self,
        lines: list[str],
        *,
        source_lang: str | None,
        target_lang: str,
        provider: str | None = None,
    ) -> TranslationAttempt:
        return self.router.translate_lines(
            lines,
            source_lang=source_lang,
            target_lang=target_lang,
            provider_name=provider,
        )

    def translate_segments(
        self,
        segments: list[SubtitleSegment],
        *,
        source_lang: str | None,
        target_lang: str,
        provider: str | None = None,
    ) -> tuple[TranslationAttempt, list[SubtitleSegment]]:
        attempt = self.translate_lines(
            [segment.text for segment in segments],
            source_lang=source_lang,
            target_lang=target_lang,
            provider=provider,
        )
        translated_segments = [
            SubtitleSegment(start=segment.start, end=segment.end, text=text)
            for segment, text in zip(segments, attempt.translations, strict=True)
        ]
        return attempt, translated_segments
