from __future__ import annotations

import gc
import threading
from pathlib import Path
from typing import Any, Dict, List, TypedDict


class TranscriptionResult(TypedDict):
    language: str
    segments: List[Dict[str, Any]]


class Transcriber:
    """WhisperX wrapper with lazy-loading and keep-alive model retention."""

    def __init__(self, model_name: str = "tiny", ttl_seconds: int = 600) -> None:
        self._model_name = model_name
        self._ttl_seconds = ttl_seconds
        self._model = None
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()

    def transcribe(self, media_path: Path) -> TranscriptionResult:
        with self._lock:
            model = self._ensure_model()
            self._reset_timer()

        result = model.transcribe(str(media_path))
        if not isinstance(result, dict):
            raise ValueError(f"Unexpected whisperx result type: {type(result)!r}")

        raw_segments = result.get("segments")
        if raw_segments is None:
            segments: List[Dict[str, Any]] = []
        elif isinstance(raw_segments, list):
            segments = raw_segments
        else:
            segments = list(raw_segments)

        return {
            "language": str(result.get("language", "unknown")),
            "segments": segments,
        }

    def _ensure_model(self):
        if self._model is not None:
            return self._model

        import whisperx

        self._model = whisperx.load_model(self._model_name, device=self._device())
        return self._model

    def _reset_timer(self) -> None:
        if self._timer:
            self._timer.cancel()
        self._timer = threading.Timer(self._ttl_seconds, self.unload)
        self._timer.daemon = True
        self._timer.start()

    def unload(self) -> None:
        with self._lock:
            self._model = None
            gc.collect()
            try:
                import torch

                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                pass

    @staticmethod
    def _device() -> str:
        try:
            import torch

            return "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            return "cpu"
