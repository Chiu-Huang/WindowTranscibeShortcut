from __future__ import annotations

import requests

from window_transcribe_shortcut.models import Segment


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

        payload = self._post_json(
            {
                "lines": lines,
                "source_lang": source_lang,
                "target_lang": target_lang,
            }
        )

        translations = payload.get("translations")
        if not isinstance(translations, list):
            raise RuntimeError("Translation service response is missing a 'translations' list.")
        return [str(item) for item in translations]

    def translate_segments(
        self,
        segments: list[Segment],
        source_lang: str | None,
        target_lang: str,
    ) -> list[Segment]:
        if not segments:
            return []

        payload = self._post_json(
            {
                "segments": [
                    {"start": segment.start, "end": segment.end, "text": segment.text}
                    for segment in segments
                ],
                "source_lang": source_lang,
                "target_lang": target_lang,
            }
        )
        translated_segments = payload.get("segments")
        if not isinstance(translated_segments, list):
            raise RuntimeError("Translation service response is missing a 'segments' list.")

        return [
            Segment(
                start=float(item["start"]),
                end=float(item["end"]),
                text=str(item["text"]),
            )
            for item in translated_segments
        ]

    def _post_json(self, payload: dict[str, object]) -> dict[str, object]:
        response = requests.post(
            f"{self.base_url}/translate",
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise RuntimeError("Translation service response was not an object.")
        return data
