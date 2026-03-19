from __future__ import annotations

from pathlib import Path

from loguru import logger

from window_transcribe_shortcut.asr import WhisperXBackend
from window_transcribe_shortcut.config import settings
from window_transcribe_shortcut.models import Segment, Transcript
from window_transcribe_shortcut.translators import DeepLTranslator
from window_transcribe_shortcut.utils import write_srt

CHINESE_LANGUAGE_CODES = {'zh', 'zh-cn', 'zh-tw'}


class TranscriptionService:
    def __init__(self) -> None:
        self.asr = WhisperXBackend(
            model_name=settings.whisper_model,
            device=settings.device,
            compute_type=settings.compute_type,
        )

    def run(self, video_path: Path, output_path: Path, source_lang: str | None, target_lang: str) -> Transcript:
        logger.info('Starting transcription for {}', video_path)
        transcript = self.asr.transcribe(video_path, language=source_lang)
        logger.info('Detected language: {}', transcript.language or 'unknown')
        logger.info('Generated {} transcript segments', len(transcript.segments))

        if self._should_translate(transcript.language, source_lang, target_lang):
            transcript = self._translate_transcript(transcript, source_lang=source_lang, target_lang=target_lang)

        write_srt(transcript, output_path)
        logger.info('Wrote subtitle file: {}', output_path)
        return transcript

    def _should_translate(self, detected_language: str | None, source_lang: str | None, target_lang: str) -> bool:
        normalized_target = target_lang.lower()
        normalized_source = (detected_language or source_lang or '').lower()
        needs_translation = normalized_source not in CHINESE_LANGUAGE_CODES
        logger.debug(
            'Translation decision: target={}, source={}, translate={}',
            normalized_target,
            normalized_source or 'unknown',
            normalized_target == 'zh' and needs_translation,
        )
        return normalized_target == 'zh' and needs_translation

    def _translate_transcript(self, transcript: Transcript, source_lang: str | None, target_lang: str) -> Transcript:
        if not settings.deepl_api_key:
            raise RuntimeError('DEEPL_API_KEY is not configured, but translation to Chinese is required.')

        logger.info('Translating transcript to {} via DeepL', target_lang)
        translator = DeepLTranslator(settings.deepl_api_key, settings.deepl_base_url)
        source = source_lang or transcript.language or None
        translated_segments = translator.translate_lines(
            [segment.text for segment in transcript.segments],
            source,
            target_lang,
        )

        if len(translated_segments) != len(transcript.segments):
            raise RuntimeError(
                'Translation backend returned a different number of lines '
                f'({len(translated_segments)}) than the transcript ({len(transcript.segments)}).'
            )

        logger.info('Translated {} subtitle lines to {}', len(translated_segments), target_lang)
        return Transcript(
            language=target_lang.lower(),
            segments=[
                Segment(start=segment.start, end=segment.end, text=text)
                for segment, text in zip(transcript.segments, translated_segments, strict=True)
            ],
        )
