from __future__ import annotations

from loguru import logger

from window_transcribe_shortcut.translators.base import TranslatorBackend


class DeepLBackend(TranslatorBackend):
    API_URL = "https://api-free.deepl.com/v2/translate"

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("DeepL API key is required (set WTS_DEEPL_API_KEY in .env).")
        self.api_key = api_key

    def translate_texts(self, texts: list[str], source_language: str, target_language: str) -> list[str]:
        import requests

        if not texts:
            return []

        source = source_language.upper()
        target = target_language.upper()
        logger.info("Translating {} segment(s): {} -> {}", len(texts), source, target)

        translated: list[str] = []
        for text in texts:
            payload = {
                "auth_key": self.api_key,
                "text": text,
                "source_lang": source,
                "target_lang": "ZH",
            }
            response = requests.post(self.API_URL, data=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            translated.append(data["translations"][0]["text"].strip())
        return translated
