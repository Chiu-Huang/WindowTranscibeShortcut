from __future__ import annotations

from pathlib import Path

from loguru import logger

from window_transcribe_shortcut.asr.whisperx_backend import WhisperXBackend
from window_transcribe_shortcut.config import settings


def main() -> int:
    sample_dir = Path("sample")
    candidates = sorted(sample_dir.glob("*.mp4"))
    if not candidates:
        raise FileNotFoundError("No .mp4 files found in sample/")

    video_path = candidates[0]
    logger.info("Running WhisperX test on: {}", video_path)

    backend = WhisperXBackend(
        model_name=settings.whisper_model,
        device=settings.whisper_device,
        model_path=str(settings.whisper_model_path) if settings.whisper_model_path else None,
    )
    result = backend.transcribe(str(video_path))

    print(f"file={video_path}")
    print(f"language={result.language}")
    print(f"segments={len(result.segments)}")
    for idx, segment in enumerate(result.segments[:5], start=1):
        print(f"[{idx}] {segment.start:.2f}-{segment.end:.2f} {segment.text}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())