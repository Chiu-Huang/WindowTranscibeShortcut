from __future__ import annotations

from pathlib import Path

from loguru import logger

from window_transcribe_shortcut.asr.base import TranscriptResult, TranscriptSegment
from window_transcribe_shortcut.asr.whisperx_backend import WhisperXBackend
from window_transcribe_shortcut.config import settings
from window_transcribe_shortcut.io_utils import build_output_path, ensure_output_dir, save_text
from window_transcribe_shortcut.subtitle_formats import to_srt
from window_transcribe_shortcut.translators.deepl_backend import DeepLBackend


def _is_chinese(language: str) -> bool:
    return language.lower().startswith("zh")


def _translated_segments(result: TranscriptResult, translated_texts: list[str]) -> list[TranscriptSegment]:
    return [
        TranscriptSegment(start=seg.start, end=seg.end, text=translated_texts[idx])
        for idx, seg in enumerate(result.segments)
    ]


def run_pipeline(video_path: str, source_language: str | None, target_language: str = "zh") -> Path:
    asr = WhisperXBackend(
        model_name=settings.whisper_model,
        device=settings.whisper_device,
        model_path=str(settings.whisper_model_path) if settings.whisper_model_path else None,
    )
    result = asr.transcribe(video_path=video_path, source_language=source_language)

    output_segments = result.segments
    if not _is_chinese(result.language):
        # Only use DeepL when a real API key is provided (not empty or the placeholder from .env.example)
        deepl_key = (settings.deepl_api_key or "").strip()
        if deepl_key and deepl_key.lower() != "your_deepl_api_key":
            logger.info("Detected language '{}' is not Chinese. Running DeepL translation.", result.language)
            translator = DeepLBackend(api_key=deepl_key)
            translated = translator.translate_texts(
                texts=[seg.text for seg in result.segments],
                source_language=result.language,
                target_language=target_language,
            )
            output_segments = _translated_segments(result, translated)
        else:
            logger.info(
                "DeepL API key not set or placeholder; skipping translation and keeping ASR text (language: '{}').",
                result.language,
            )
    else:
        logger.info("Detected language '{}' is Chinese. Skip translation.", result.language)

    output_dir = ensure_output_dir(settings.output_dir)
    output_path = build_output_path(Path(video_path), output_dir)
    save_text(output_path, to_srt(output_segments))
    return output_path
