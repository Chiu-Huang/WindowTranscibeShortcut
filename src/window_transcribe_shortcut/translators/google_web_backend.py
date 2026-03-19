from __future__ import annotations

import requests

from window_transcribe_shortcut.translators.base import Translator

_LANG_MAP = {
    "zh": "zh-CN",
    "zh-cn": "zh-CN",
    "zh-tw": "zh-TW",
}


class GoogleWebTranslator(Translator):
    service_name = "google_web"

    def __init__(self, base_url: str) -> None:
        self.url = base_url.rstrip("/")

    def is_available(self) -> tuple[bool, str | None]:
        return True, None

    def translate_lines(
        self, lines: list[str], source_lang: str | None, target_lang: str
    ) -> list[str]:
        if not lines:
            return []

        translated_lines: list[str] = []
        target = _LANG_MAP.get(target_lang.lower(), target_lang)
        source = "auto" if not source_lang else _LANG_MAP.get(source_lang.lower(), source_lang)

        for line in lines:
            params = {
                "client": "gtx",
                "sl": source,
                "tl": target,
                "dt": "t",
                "q": line,
            }
            response = requests.get(self.url, params=params, timeout=30)
            response.raise_for_status()
            payload = response.json()
            translated_text = "".join(
                chunk[0] for chunk in payload[0] if chunk and chunk[0]
            )
            translated_lines.append(translated_text)

        return translated_lines
