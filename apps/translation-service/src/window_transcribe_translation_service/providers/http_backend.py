from __future__ import annotations

import requests

from window_transcribe_translation_service.providers.base import TranslationProvider, TranslationProviderError


class HTTPTranslationProvider(TranslationProvider):
    name = "http"
    description = "External HTTP translation backend"

    def __init__(self, url: str, enabled: bool, timeout_seconds: float) -> None:
        self.url = url
        self._enabled = enabled
        self.timeout_seconds = timeout_seconds

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def configured(self) -> bool:
        return bool(self.url)

    def translate_lines(self, lines: list[str], source_lang: str | None, target_lang: str) -> list[str]:
        if not self.enabled:
            raise TranslationProviderError(
                self.name,
                "HTTP translation backend is disabled.",
                error_type="configuration_error",
            )
        if not self.configured:
            raise TranslationProviderError(
                self.name,
                "HTTP translation backend URL is missing.",
                error_type="configuration_error",
            )
        if not lines:
            return []

        try:
            response = requests.post(
                self.url,
                json={
                    "lines": lines,
                    "source_lang": source_lang,
                    "target_lang": target_lang,
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.Timeout as exc:
            raise TranslationProviderError(
                self.name,
                "HTTP translation backend timed out.",
                error_type="timeout",
                retryable=True,
            ) from exc
        except requests.HTTPError as exc:
            detail = exc.response.text.strip() if exc.response is not None else str(exc)
            raise TranslationProviderError(
                self.name,
                f"HTTP translation backend failed: {detail}",
                error_type="http_error",
                retryable=exc.response is None or exc.response.status_code >= 500,
            ) from exc
        except requests.RequestException as exc:
            raise TranslationProviderError(
                self.name,
                f"HTTP translation backend request failed: {exc}",
                error_type="network_error",
                retryable=True,
            ) from exc
        except ValueError as exc:
            raise TranslationProviderError(
                self.name,
                "HTTP translation backend returned invalid JSON.",
                error_type="invalid_response",
            ) from exc

        translations = payload.get("translations")
        if not isinstance(translations, list):
            raise TranslationProviderError(
                self.name,
                "HTTP translation backend response is missing a 'translations' list.",
                error_type="invalid_response",
            )
        return [str(item) for item in translations]
