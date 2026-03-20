from __future__ import annotations

from loguru import logger

from window_transcribe_translation_service.config import settings
from window_transcribe_translation_service.translators import (
    DeepLTranslator,
    HTTPTranslationServiceTranslator,
)


class TranslationService:
    def translate_lines(
        self,
        lines: list[str],
        source_lang: str | None,
        target_lang: str,
    ) -> list[str]:
        deepl_configured = bool(
            settings.deepl_api_key and settings.deepl_api_key != "your_deepl_api_key"
        )

        if deepl_configured:
            logger.info("Translating transcript to {} via DeepL", target_lang)
            translator = DeepLTranslator(settings.deepl_api_key, settings.deepl_base_url)
            try:
                return translator.translate_lines(lines, source_lang, target_lang)
            except Exception as exc:
                if not settings.local_translation_enabled:
                    raise RuntimeError(f"DeepL translation failed: {exc}") from exc
                logger.warning(
                    "DeepL translation failed ({}). Falling back to local translation service.",
                    exc,
                )
        else:
            logger.info("DeepL is not configured; checking local translation fallback.")

        if not settings.local_translation_enabled:
            raise RuntimeError("No translation backend is available.")

        logger.info(
            "Translating transcript to {} via local translation service at {}",
            target_lang,
            settings.local_translation_url,
        )
        translator = HTTPTranslationServiceTranslator(
            settings.local_translation_url,
            timeout_seconds=settings.translation_request_timeout_seconds,
        )
        try:
            return translator.translate_lines(lines, source_lang, target_lang)
        except Exception as exc:
            raise RuntimeError(f"Local translation service failed: {exc}") from exc
