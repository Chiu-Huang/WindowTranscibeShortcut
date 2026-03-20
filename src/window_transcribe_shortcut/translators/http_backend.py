from __future__ import annotations

import requests

from shared.contracts import TranslateRequest, TranslateResponse
from window_transcribe_shortcut.translators.base import Translator


class HTTPTranslationServiceTranslator(Translator):
    def __init__(self, base_url: str, timeout_seconds: float = 60.0) -> None:
        self.url = base_url
        self.timeout_seconds = timeout_seconds

    def translate_lines(self, lines: list[str], source_lang: str | None, target_lang: str) -> list[str]:
        if not lines:
            return []

        request_model = TranslateRequest(
            lines=lines,
            source_language=source_lang or "auto",
            target_language=target_lang,
        )
        response = requests.post(
            self.url,
            json=request_model.model_dump(mode="json"),
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = TranslateResponse.model_validate(response.json())
        if payload.translated_lines is None:
            raise RuntimeError("Local translation service response did not include translated_lines.")
        return payload.translated_lines
