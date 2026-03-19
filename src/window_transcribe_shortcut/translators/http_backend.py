from __future__ import annotations

import requests

from window_transcribe_shortcut.translators.base import Translator


class HTTPTranslationServiceTranslator(Translator):
    def __init__(self, base_url: str, timeout_seconds: float = 60.0) -> None:
        self.url = base_url
        self.timeout_seconds = timeout_seconds

    def translate_lines(self, lines: list[str], source_lang: str | None, target_lang: str) -> list[str]:
        if not lines:
            return []

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
        translations = payload.get("translations")
        if not isinstance(translations, list):
            raise RuntimeError("Local translation service response is missing a 'translations' list.")
        return [str(item) for item in translations]
