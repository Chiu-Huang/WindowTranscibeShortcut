from __future__ import annotations

from fastapi import FastAPI, HTTPException
from loguru import logger

from window_transcribe_shortcut.api_models import (
    HealthResponse,
    SegmentResponse,
    TranscriptionRequest,
    TranscriptionResponse,
)
from window_transcribe_shortcut.config import settings
from window_transcribe_shortcut.pipeline import TranscriptionService
from window_transcribe_shortcut.presets import PRESETS
from window_transcribe_shortcut.utils import ensure_video_file, resolve_output_path

service = TranscriptionService()


def create_app() -> FastAPI:
    app = FastAPI(
        title='Window Transcribe Shortcut API',
        version='0.2.0',
        description='Persistent FastAPI backend for WhisperX transcription and subtitle translation.',
    )

    @app.get('/health', response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            status='ok',
            model_loaded=service.is_model_loaded,
            model_name=settings.whisper_model,
            device=settings.device,
            output_dir=settings.output_dir,
        )

    @app.get('/presets')
    def presets() -> list[dict[str, str | None]]:
        return [
            {
                'name': preset.name,
                'description': preset.description,
                'source_lang': preset.source_lang,
                'target_lang': preset.target_lang,
            }
            for preset in PRESETS.values()
        ]

    @app.post('/warmup', response_model=HealthResponse)
    def warmup() -> HealthResponse:
        logger.info('Warming up WhisperX backend')
        service.preload_model()
        return health()

    @app.post('/transcribe', response_model=TranscriptionResponse)
    def transcribe(request: TranscriptionRequest) -> TranscriptionResponse:
        try:
            preset = PRESETS[request.preset]
        except KeyError as exc:
            raise HTTPException(status_code=400, detail=f'Unknown preset: {request.preset}') from exc

        try:
            video = ensure_video_file(request.video)
            output = resolve_output_path(video, request.output, settings.output_dir)
            transcript = service.run(
                video,
                output,
                source_lang=preset.source_lang,
                target_lang=preset.target_lang,
            )
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:  # pragma: no cover - defensive API boundary
            logger.exception('Unhandled API transcription failure: {}', exc)
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        detected_language = transcript.language or preset.source_lang or 'unknown'
        return TranscriptionResponse(
            preset=preset.name,
            source_language=preset.source_lang or 'auto',
            target_language=preset.target_lang,
            detected_language=detected_language,
            video=video,
            output=output,
            subtitle_line_count=len(transcript.segments),
            segments=[
                SegmentResponse(start=segment.start, end=segment.end, text=segment.text)
                for segment in transcript.segments
            ],
        )

    return app


app = create_app()
