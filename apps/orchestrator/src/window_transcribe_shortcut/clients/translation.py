from __future__ import annotations

import requests


class TranslationServiceClient:
    def __init__(self, base_url: str, timeout_seconds: float = 300.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def translate_lines(
        self,
        lines: list[str],
        source_lang: str | None,
        target_lang: str,
    ) -> list[str]:
        if not lines:
            return []

        response = requests.post(
            f"{self.base_url}/translate",
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
            raise RuntimeError("Translation service response is missing a 'translations' list.")
        return [str(item) for item in translations]
