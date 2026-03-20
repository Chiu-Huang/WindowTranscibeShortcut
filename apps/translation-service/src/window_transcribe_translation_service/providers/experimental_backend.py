from __future__ import annotations

from window_transcribe_translation_service.providers.base import TranslationProvider, TranslationProviderError


class ExperimentalTranslationProvider(TranslationProvider):
    def __init__(self, name: str, description: str, enabled: bool, configured: bool) -> None:
        self.name = name
        self.description = description
        self._enabled = enabled
        self._configured = configured

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def configured(self) -> bool:
        return self._configured

    def translate_lines(self, lines: list[str], source_lang: str | None, target_lang: str) -> list[str]:
        if not self.enabled:
            raise TranslationProviderError(
                self.name,
                f"Provider '{self.name}' is disabled.",
                error_type="configuration_error",
            )
        if not self.configured:
            raise TranslationProviderError(
                self.name,
                f"Provider '{self.name}' is not configured.",
                error_type="configuration_error",
            )
        raise TranslationProviderError(
            self.name,
            f"Provider '{self.name}' is not implemented yet.",
            error_type="not_implemented",
        )
