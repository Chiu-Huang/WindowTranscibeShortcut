from __future__ import annotations

import requests

from window_transcribe_shortcut.translators.base import Translator

_LANG_MAP = {
    "en": "EN",
    "ja": "JA",
    "zh": "ZH",
    "zh-cn": "ZH",
    "zh-tw": "ZH",
}


class DeepLTranslator(Translator):
    def __init__(self, api_key: str, base_url: str) -> None:
        self.api_key = api_key
        self.url = f"{base_url.rstrip('/')}/translate"

    def translate_lines(self, lines: list[str], source_lang: str | None, target_lang: str) -> list[str]:
        if not lines:
            return []
        payload: dict[str, object] = {
            "auth_key": self.api_key,
            "text": lines,
            "target_lang": _LANG_MAP.get(target_lang.lower(), target_lang.upper()),
        }
        if source_lang:
            payload["source_lang"] = _LANG_MAP.get(source_lang.lower(), source_lang.upper())

        resp = requests.post(self.url, data=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return [item["text"] for item in data.get("translations", [])]
