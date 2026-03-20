from __future__ import annotations

from pathlib import Path

import requests

from window_transcribe_shortcut.models import Segment, Transcript


class TranscribeServiceClient:
    def __init__(self, base_url: str, timeout_seconds: float = 300.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def health(self) -> dict[str, object]:
        response = requests.get(f"{self.base_url}/health", timeout=self.timeout_seconds)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise RuntimeError("Transcribe service health response was not an object.")
        return payload

    def preload(self, source_lang: str | None = None) -> dict[str, object]:
        response = requests.post(
            f"{self.base_url}/warmup",
            json={"source_lang": source_lang},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise RuntimeError("Transcribe service warmup response was not an object.")
        return payload

    def transcribe(self, video_path: Path, source_lang: str | None) -> Transcript:
        response = requests.post(
            f"{self.base_url}/transcribe",
            json={"video": str(video_path), "source_lang": source_lang},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
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
