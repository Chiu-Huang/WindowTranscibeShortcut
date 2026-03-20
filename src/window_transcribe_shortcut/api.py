from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from loguru import logger

from pydantic import BaseModel

from shared.contracts import (
    ErrorDetail,
    JobMetadata,
    OrchestratorJobResponse,
    ServiceStageStatus,
    TranscribeRequest,
    TranslateRequest,
    TranslateResponse,
    TranslatedSubtitleSegment,
)
from window_transcribe_shortcut.config import settings
from window_transcribe_shortcut.pipeline import TranscriptionService
from window_transcribe_shortcut.presets import PRESETS
from window_transcribe_shortcut.utils import ensure_video_file, resolve_output_path

service = TranscriptionService()


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_name: str
    device: str
    output_dir: Path


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

    @app.post('/transcribe', response_model=OrchestratorJobResponse)
    def transcribe(request: TranscribeRequest) -> OrchestratorJobResponse:
        metadata: JobMetadata = request.metadata
        preset_name = metadata.preset
        preset = PRESETS.get(preset_name) if preset_name else None
        if preset_name and preset is None:
            raise HTTPException(status_code=400, detail=f'Unknown preset: {preset_name}')

        source_language_hint = request.source_language_hint or (preset.source_lang if preset else None)
        target_language = preset.target_lang if preset else 'zh'
        video = ensure_video_file(request.input_file_path)
        output = resolve_output_path(video, None, settings.output_dir)
        try:
            transcript, translation_applied = service.run(
                video,
                output,
                source_lang=source_language_hint,
                target_lang=target_language,
            )
            transcribe_response = service.build_transcribe_response(
                transcript=transcript,
                input_file_path=video,
                source_lang=source_language_hint,
                output_subtitle_path=output,
            )
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except RuntimeError as exc:
            logger.warning('Transcription job failed: {}', exc)
            return OrchestratorJobResponse(
                status='failed',
                output_subtitle_path=output,
                stages=[
                    ServiceStageStatus(stage='transcription', status='failed', detail=str(exc)),
                    ServiceStageStatus(stage='translation', status='skipped', detail='Skipped after transcription failure.'),
                    ServiceStageStatus(stage='subtitle_write', status='skipped', detail='Skipped after transcription failure.'),
                ],
                error=ErrorDetail(stage='transcription', message=str(exc), error_type=type(exc).__name__),
            )
        except Exception as exc:  # pragma: no cover - defensive API boundary
            logger.exception('Unhandled API transcription failure: {}', exc)
            return OrchestratorJobResponse(
                status='failed',
                output_subtitle_path=output,
                stages=[
                    ServiceStageStatus(stage='transcription', status='failed', detail=str(exc)),
                    ServiceStageStatus(stage='translation', status='skipped', detail='Skipped after internal error.'),
                    ServiceStageStatus(stage='subtitle_write', status='skipped', detail='Skipped after internal error.'),
                ],
                error=ErrorDetail(stage='transcription', message=str(exc), error_type=type(exc).__name__),
            )

        stage_statuses = [
            ServiceStageStatus(stage='transcription', status='completed'),
            ServiceStageStatus(
                stage='translation',
                status='completed' if translation_applied else 'skipped',
                detail=None if translation_applied else 'Source language already matched target language.',
            ),
            ServiceStageStatus(stage='subtitle_write', status='completed'),
        ]
        return OrchestratorJobResponse(
            status='completed',
            output_subtitle_path=output,
            stages=stage_statuses,
            transcription=transcribe_response,
        )

    @app.post('/translate', response_model=TranslateResponse)
    def translate(request: TranslateRequest) -> TranslateResponse:
        if request.lines is not None:
            translated_lines = service._translate_lines(
                request.lines,
                source_lang=request.source_language,
                target_lang=request.target_language,
            )
            if translated_lines is None:
                raise HTTPException(status_code=503, detail='No translation backend is available.')
            return TranslateResponse(
                translated_lines=translated_lines,
                requested_count=request.item_count,
                translated_count=len(translated_lines),
            )

        translated_segments = service.translate_segments(
            request.segments or [],
            source_lang=request.source_language,
            target_lang=request.target_language,
        )
        return TranslateResponse(
            translated_segments=[
                TranslatedSubtitleSegment(
                    start=segment.start,
                    end=segment.end,
                    text=segment.text,
                    original_text=original.text,
                )
                for original, segment in zip(request.segments or [], translated_segments, strict=True)
            ],
            requested_count=request.item_count,
            translated_count=len(translated_segments),
        )

    return app


app = create_app()
