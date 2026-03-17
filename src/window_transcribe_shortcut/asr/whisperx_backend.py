from __future__ import annotations

from pathlib import Path

from loguru import logger

from window_transcribe_shortcut.asr.base import ASRBackend
from window_transcribe_shortcut.models import Segment, Transcript


class WhisperXBackend(ASRBackend):
    def __init__(self, model_name: str, device: str, compute_type: str) -> None:
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type

    def transcribe(self, video_path: Path, language: str | None = None) -> Transcript:
        import whisperx

        logger.info("Loading WhisperX model '{}' on {}", self.model_name, self.device)
        model = whisperx.load_model(
            self.model_name,
            self.device,
            compute_type=self.compute_type,
            language=language,
        )
        audio = whisperx.load_audio(str(video_path))
        result = model.transcribe(audio, language=language)

        detected = (result.get("language") or language or "").lower()
        segments = [
            Segment(
                start=float(seg.get("start", 0.0)),
                end=float(seg.get("end", 0.0)),
                text=str(seg.get("text", "")).strip(),
            )
            for seg in result.get("segments", [])
        ]
        return Transcript(language=detected, segments=segments)
