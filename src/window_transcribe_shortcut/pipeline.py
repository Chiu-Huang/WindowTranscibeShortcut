from __future__ import annotations

from pathlib import Path

from loguru import logger

from window_transcribe_shortcut.asr import WhisperXBackend
from window_transcribe_shortcut.config import settings
from window_transcribe_shortcut.models import Segment, Transcript
from window_transcribe_shortcut.subtitle_formats import write_srt
from window_transcribe_shortcut.translators import DeepLTranslator


class TranscriptionService:
    def __init__(self) -> None:
        self.asr = WhisperXBackend(
            model_name=settings.whisper_model,
            device=settings.device,
            compute_type=settings.compute_type,
        )

    def run(self, video_path: Path, output_path: Path, source_lang: str | None, target_lang: str) -> Transcript:
        transcript = self.asr.transcribe(video_path, language=source_lang)
        logger.info("Detected language: {}", transcript.language)

        needs_translation = (transcript.language or source_lang or "").lower() not in {"zh", "zh-cn", "zh-tw"}
        if target_lang.lower() == "zh" and needs_translation:
            if not settings.deepl_api_key:
                raise RuntimeError("DEEPL_API_KEY is not configured, but translation to Chinese is required.")
            translator = DeepLTranslator(settings.deepl_api_key, settings.deepl_base_url)
            source = source_lang or transcript.language or None
            translated = translator.translate_lines([seg.text for seg in transcript.segments], source, target_lang)
            transcript = Transcript(
                language="zh",
                segments=[
                    Segment(start=seg.start, end=seg.end, text=text)
                    for seg, text in zip(transcript.segments, translated, strict=False)
                ],
            )
            logger.info("Translated {} subtitle lines to Chinese", len(transcript.segments))

        write_srt(transcript, output_path)
        logger.info("Wrote subtitle file: {}", output_path)
        return transcript
