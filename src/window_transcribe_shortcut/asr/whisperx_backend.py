from __future__ import annotations

from loguru import logger

from window_transcribe_shortcut.asr.base import ASRBackend, TranscriptResult, TranscriptSegment


class WhisperXBackend(ASRBackend):
    def __init__(self, model_name: str, device: str = "cpu", model_path: str | None = None) -> None:
        self.model_name = model_name
        self.device = device
        self.model_path = model_path

    def transcribe(self, video_path: str, source_language: str | None = None) -> TranscriptResult:
        import whisperx

        if self.model_path:
            logger.info(
                "Loading WhisperX model='{}' on device='{}' using model_path='{}'",
                self.model_name,
                self.device,
                self.model_path,
            )
        else:
            logger.info("Loading WhisperX model='{}' on device='{}'", self.model_name, self.device)
        model = whisperx.load_model(self.model_name, self.device, download_root=self.model_path)
        logger.info("Transcribing: {}", video_path)
        result = model.transcribe(video_path, language=source_language)
        segments = [
            TranscriptSegment(
                start=float(seg["start"]),
                end=float(seg["end"]),
                text=str(seg["text"]).strip(),
            )
            for seg in result.get("segments", [])
        ]
        language = result.get("language") or (source_language or "unknown")
        return TranscriptResult(language=language, segments=segments)
