from __future__ import annotations

from pathlib import Path

import requests

from window_transcribe_shortcut.models import Segment, Transcript


class TranscribeServiceClient:
    def __init__(self, base_url: str, timeout_seconds: float = 300.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def health(self) -> dict[str, object]:
        return self._get_json("/health", "health")

    def preload(self, source_lang: str | None = None) -> dict[str, object]:
        return self._post_json(
            "/warmup",
            {"source_lang": source_lang},
            "warmup",
        )

    def transcribe(self, video_path: Path, source_lang: str | None) -> Transcript:
        payload = self._post_json(
            "/transcribe",
            {"video": str(video_path), "source_lang": source_lang},
            "transcription",
        )

        segments = payload.get("segments")
        if not isinstance(segments, list):
            raise RuntimeError("Transcribe service response is missing a 'segments' list.")

        language = str(payload.get("detected_language") or source_lang or "")
        return Transcript(
            language=language,
            segments=[
                Segment(
                    start=float(segment.get("start", 0.0)),
                    end=float(segment.get("end", 0.0)),
                    text=str(segment.get("text", "")).strip(),
                )
                for segment in segments
                if isinstance(segment, dict)
            ],
        )

    def _get_json(self, path: str, operation: str) -> dict[str, object]:
        response = requests.get(f"{self.base_url}{path}", timeout=self.timeout_seconds)
        response.raise_for_status()
        return self._decode_json_object(response, operation)

    def _post_json(
        self,
        path: str,
        payload: dict[str, object],
        operation: str,
    ) -> dict[str, object]:
        response = requests.post(
            f"{self.base_url}{path}",
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return self._decode_json_object(response, operation)

    @staticmethod
    def _decode_json_object(response: requests.Response, operation: str) -> dict[str, object]:
        payload = response.json()
        if not isinstance(payload, dict):
            raise RuntimeError(f"Transcribe service {operation} response was not an object.")
        return payload
