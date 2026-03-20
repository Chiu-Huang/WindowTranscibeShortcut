from __future__ import annotations

from window_transcribe_translation_service.config import Settings
from window_transcribe_translation_service.providers.base import (
    ProviderDescriptor,
    TranslationAttempt,
    TranslationProvider,
    TranslationProviderError,
    TranslationServiceError,
)
from window_transcribe_translation_service.providers.deepl_backend import DeepLTranslationProvider
from window_transcribe_translation_service.providers.experimental_backend import ExperimentalTranslationProvider
from window_transcribe_translation_service.providers.http_backend import HTTPTranslationProvider


class ProviderRouter:
    def __init__(self, providers: list[TranslationProvider], provider_order: list[str]) -> None:
        self.providers = {provider.name: provider for provider in providers}
        self.provider_order = provider_order

    @classmethod
    def from_settings(cls, settings: Settings) -> "ProviderRouter":
        providers: list[TranslationProvider] = [
            DeepLTranslationProvider(
                api_key=settings.deepl_api_key,
                base_url=settings.deepl_base_url,
                timeout_seconds=settings.translation_request_timeout_seconds,
            ),
            HTTPTranslationProvider(
                url=settings.http_translation_url,
                enabled=settings.http_translation_enabled,
                timeout_seconds=settings.translation_request_timeout_seconds,
            ),
            ExperimentalTranslationProvider(
                name="hf_nllb",
                description=(
                    "Experimental Hugging Face/NLLB backend placeholder; configuration lives only in this service."
                ),
                enabled=settings.huggingface_nllb_enabled,
                configured=bool(settings.huggingface_nllb_url),
            ),
        ]
        return cls(providers=providers, provider_order=settings.translation_provider_order)

    def list_providers(self) -> list[ProviderDescriptor]:
        return [
            self.providers[name].describe(priority=index)
            for index, name in enumerate(self.provider_order, start=1)
            if name in self.providers
        ]

    def translate_lines(
        self,
        lines: list[str],
        *,
        source_lang: str | None,
        target_lang: str,
        provider_name: str | None = None,
    ) -> TranslationAttempt:
        provider_names = [provider_name] if provider_name else self.provider_order
        failures = []

        for name in provider_names:
            provider = self.providers.get(name)
            if provider is None:
                failures.append(
                    TranslationProviderError(
                        name,
                        f"Unknown provider '{name}'.",
                        error_type="unknown_provider",
                    ).to_failure()
                )
                continue

            try:
                translations = provider.translate_lines(lines, source_lang, target_lang)
            except TranslationProviderError as exc:
                failures.append(exc.to_failure())
                continue

            if len(translations) != len(lines):
                failures.append(
                    TranslationProviderError(
                        name,
                        "Provider returned a different number of translations than requested.",
                        error_type="invalid_response",
                    ).to_failure()
                )
                continue

            return TranslationAttempt(provider=name, translations=translations, failures=failures)

        if provider_name:
            message = f"Translation provider '{provider_name}' failed."
        else:
            message = "All translation providers failed."
        raise TranslationServiceError(message, failures=failures)
