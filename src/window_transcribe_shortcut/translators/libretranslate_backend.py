from __future__ import annotations

import requests

from window_transcribe_shortcut.translators.base import (
    TranslationUnavailableError,
    Translator,
)

_LANG_MAP = {
    "zh": "zh",
    "zh-cn": "zh",
    "zh-tw": "zt",
}


class LibreTranslateTranslator(Translator):
    service_name = "libretranslate"

    def __init__(self, base_url: str | None, api_key: str | None) -> None:
        self.base_url = base_url.rstrip("/") if base_url else None
        self.api_key = api_key

    def is_available(self) -> tuple[bool, str | None]:
        if self.base_url:
            return True, None
        return False, "LIBRETRANSLATE_BASE_URL is not configured"

    def translate_lines(
        self, lines: list[str], source_lang: str | None, target_lang: str
    ) -> list[str]:
        available, reason = self.is_available()
        if not available or self.base_url is None:
            raise TranslationUnavailableError(reason or "LibreTranslate is unavailable")
        if not lines:
            return []

        translated_lines: list[str] = []
        endpoint = f"{self.base_url}/translate"
        source = source_lang or "auto"
        target = _LANG_MAP.get(target_lang.lower(), target_lang.lower())
        for line in lines:
            payload: dict[str, object] = {
                "q": line,
                "source": source,
                "target": target,
                "format": "text",
            }
            if self.api_key:
                payload["api_key"] = self.api_key
            response = requests.post(endpoint, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            translated_lines.append(data["translatedText"])
        return translated_lines
