from __future__ import annotations

import requests

from window_transcribe_translation_service.providers.base import TranslationProvider, TranslationProviderError

_LANG_MAP = {
    "en": "EN",
    "ja": "JA",
    "zh": "ZH",
    "zh-cn": "ZH",
    "zh-tw": "ZH",
}


class DeepLTranslationProvider(TranslationProvider):
    name = "deepl"
    description = "DeepL API"

    def __init__(self, api_key: str | None, base_url: str, timeout_seconds: float) -> None:
        self.api_key = api_key
        self.url = f"{base_url.rstrip('/')}/translate"
        self.timeout_seconds = timeout_seconds

    @property
    def enabled(self) -> bool:
        return True

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.api_key != "your_deepl_api_key")

    def translate_lines(self, lines: list[str], source_lang: str | None, target_lang: str) -> list[str]:
        if not self.configured:
            raise TranslationProviderError(
                self.name,
                "DeepL is not configured.",
                error_type="configuration_error",
            )
        if not lines:
            return []

        payload: dict[str, object] = {
            "auth_key": self.api_key,
            "text": lines,
            "target_lang": _LANG_MAP.get(target_lang.lower(), target_lang.upper()),
        }
        if source_lang:
            payload["source_lang"] = _LANG_MAP.get(source_lang.lower(), source_lang.upper())

        try:
            response = requests.post(self.url, data=payload, timeout=self.timeout_seconds)
            response.raise_for_status()
            data = response.json()
        except requests.Timeout as exc:
            raise TranslationProviderError(
                self.name,
                "DeepL timed out.",
                error_type="timeout",
                retryable=True,
            ) from exc
        except requests.HTTPError as exc:
            detail = exc.response.text.strip() if exc.response is not None else str(exc)
            raise TranslationProviderError(
                self.name,
                f"DeepL request failed: {detail}",
                error_type="http_error",
                retryable=exc.response is None or exc.response.status_code >= 500,
            ) from exc
        except requests.RequestException as exc:
            raise TranslationProviderError(
                self.name,
                f"DeepL request failed: {exc}",
                error_type="network_error",
                retryable=True,
            ) from exc
        except ValueError as exc:
            raise TranslationProviderError(
                self.name,
                "DeepL returned invalid JSON.",
                error_type="invalid_response",
            ) from exc

        translations = data.get("translations")
        if not isinstance(translations, list):
            raise TranslationProviderError(
                self.name,
                "DeepL response is missing a 'translations' list.",
                error_type="invalid_response",
            )

        return [str(item.get("text", "")) for item in translations]
