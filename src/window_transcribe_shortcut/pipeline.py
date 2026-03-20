from __future__ import annotations

from pathlib import Path

from loguru import logger

from window_transcribe_shortcut.asr import WhisperXBackend
from window_transcribe_shortcut.config import settings
from window_transcribe_shortcut.models import Segment, Transcript
from shared.contracts import RawTranscriptMetadata, SubtitleSegment, TranscribeResponse, TranslateRequest
from window_transcribe_shortcut.translators import DeepLTranslator, HTTPTranslationServiceTranslator
from window_transcribe_shortcut.utils import write_srt

CHINESE_LANGUAGE_CODES = {"zh", "zh-cn", "zh-tw"}


class TranscriptionService:
    def __init__(self) -> None:
        self.asr = WhisperXBackend(
            model_name=settings.whisper_model,
            device=settings.device,
            compute_type=settings.compute_type,
        )

    @property
    def is_model_loaded(self) -> bool:
        return self.asr.is_loaded

    def preload_model(self, source_lang: str | None = None) -> None:
        self.asr.preload(language=source_lang)

    def run(
        self,
        video_path: Path,
        output_path: Path,
        source_lang: str | None,
        target_lang: str,
    ) -> tuple[Transcript, bool]:
        logger.info("Starting transcription for {}", video_path)
        transcript = self.asr.transcribe(video_path, language=source_lang)
        logger.info("Detected language: {}", transcript.language or "unknown")
        logger.info("Generated {} transcript segments", len(transcript.segments))

        translation_applied = False
        if self._should_translate(transcript.language, source_lang, target_lang):
            transcript = self._translate_transcript(
                transcript, source_lang=source_lang, target_lang=target_lang
            )
            translation_applied = True

        write_srt(transcript, output_path)
        logger.info("Wrote subtitle file: {}", output_path)
        return transcript, translation_applied

    def transcribe_only(self, video_path: Path, source_lang: str | None) -> TranscribeResponse:
        logger.info("Starting transcription for {}", video_path)
        transcript = self.asr.transcribe(video_path, language=source_lang)
        logger.info("Detected language: {}", transcript.language or "unknown")
        logger.info("Generated {} transcript segments", len(transcript.segments))
        return self.build_transcribe_response(
            transcript=transcript,
            input_file_path=video_path,
            source_lang=source_lang,
        )

    def translate_segments(
        self,
        segments: list[SubtitleSegment],
        source_lang: str,
        target_lang: str,
    ) -> list[SubtitleSegment]:
        request = TranslateRequest(
            segments=segments,
            source_language=source_lang,
            target_language=target_lang,
        )
        translated_lines = self._translate_lines(
            [segment.text for segment in request.segments or []],
            source_lang=request.source_language,
            target_lang=request.target_language,
        )
        if translated_lines is None:
            raise RuntimeError("No translation backend is available.")
        if len(translated_lines) != len(segments):
            raise RuntimeError(
                "Translation backend returned a different number of lines "
                f"({len(translated_lines)}) than requested ({len(segments)})."
            )
        return [
            SubtitleSegment(start=segment.start, end=segment.end, text=text)
            for segment, text in zip(segments, translated_lines, strict=True)
        ]

    def _should_translate(
        self, detected_language: str | None, source_lang: str | None, target_lang: str
    ) -> bool:
        normalized_target = target_lang.lower()
        normalized_source = (detected_language or source_lang or "").lower()
        needs_translation = normalized_source not in CHINESE_LANGUAGE_CODES
        logger.debug(
            "Translation decision: target={}, source={}, translate={}",
            normalized_target,
            normalized_source or "unknown",
            normalized_target == "zh" and needs_translation,
        )
        return normalized_target == "zh" and needs_translation

    def _translate_transcript(
        self, transcript: Transcript, source_lang: str | None, target_lang: str
    ) -> Transcript:
        source = source_lang or transcript.language or None
        translated_segments = self._translate_lines(
            [segment.text for segment in transcript.segments],
            source_lang=source,
            target_lang=target_lang,
        )

        if translated_segments is None:
            logger.warning(
                "No translation backend is available. Returning original transcript without translation."
            )
            return transcript

        if len(translated_segments) != len(transcript.segments):
            raise RuntimeError(
                "Translation backend returned a different number of lines "
                f"({len(translated_segments)}) than the transcript ({len(transcript.segments)})."
            )

        logger.info(
            "Translated {} subtitle lines to {}", len(translated_segments), target_lang
        )
        return Transcript(
            language=target_lang.lower(),
            segments=[
                Segment(start=segment.start, end=segment.end, text=text)
                for segment, text in zip(
                    transcript.segments, translated_segments, strict=True
                )
            ],
        )

    def _translate_lines(
        self,
        lines: list[str],
        source_lang: str | None,
        target_lang: str,
    ) -> list[str] | None:
        deepl_configured = bool(
            settings.deepl_api_key and settings.deepl_api_key != "your_deepl_api_key"
        )

        if deepl_configured:
            logger.info("Translating transcript to {} via DeepL", target_lang)
            translator = DeepLTranslator(settings.deepl_api_key, settings.deepl_base_url)
            try:
                return translator.translate_lines(lines, source_lang, target_lang)
            except Exception as exc:
                if not settings.local_translation_enabled:
                    raise RuntimeError(f"DeepL translation failed: {exc}") from exc
                logger.warning(
                    "DeepL translation failed ({}). Falling back to local translation service.",
                    exc,
                )
        else:
            logger.info("DeepL is not configured; checking local translation fallback.")

        if not settings.local_translation_enabled:
            return None

        logger.info(
            "Translating transcript to {} via local translation service at {}",
            target_lang,
            settings.local_translation_url,
        )
        translator = HTTPTranslationServiceTranslator(
            settings.local_translation_url,
            timeout_seconds=settings.translation_request_timeout_seconds,
        )
        try:
            return translator.translate_lines(lines, source_lang, target_lang)
        except Exception as exc:
            raise RuntimeError(f"Local translation service failed: {exc}") from exc

    def build_transcribe_response(
        self,
        transcript: Transcript,
        input_file_path: Path,
        source_lang: str | None,
        output_subtitle_path: Path | None = None,
    ) -> TranscribeResponse:
        detected_language = transcript.language or source_lang or "unknown"
        segments = [
            SubtitleSegment(start=segment.start, end=segment.end, text=segment.text)
            for segment in transcript.segments
        ]
        return TranscribeResponse(
            detected_language=detected_language,
            segments=segments,
            raw_transcript_metadata=RawTranscriptMetadata(
                provider="whisperx",
                input_file_path=input_file_path,
                segment_count=len(segments),
                language_hint=source_lang,
                model_name=settings.whisper_model,
                output_subtitle_path=output_subtitle_path,
            ),
        )


if __name__ == "__main__":
    print(settings.model_dump_json(indent=4))
