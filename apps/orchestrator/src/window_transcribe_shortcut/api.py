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
from window_transcribe_shortcut.utils import resolve_output_path

service = TranscriptionService()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Window Transcribe Shortcut API",
        version="0.4.0",
        description="Orchestrator API coordinating the transcribe and translation services.",
    )

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            model_loaded=service.is_model_loaded,
            transcribe_service_url=settings.transcribe_service_url,
            translation_service_url=settings.translation_service_url,
            output_dir=settings.output_dir,
        )

    @app.get("/presets")
    def presets() -> list[dict[str, str | None]]:
        return [
            {
                "name": preset.name,
                "description": preset.description,
                "source_lang": preset.source_lang,
                "target_lang": preset.target_lang,
            }
            for preset in PRESETS.values()
        ]

    @app.post("/warmup", response_model=HealthResponse)
    def warmup() -> HealthResponse:
        logger.info("Warming up transcribe service through orchestrator")
        service.preload_model()
        return health()

    @app.post("/transcribe", response_model=TranscriptionResponse)
    def transcribe(request: TranscriptionRequest) -> TranscriptionResponse:
        try:
            preset = PRESETS[request.preset]
        except KeyError as exc:
            raise HTTPException(status_code=400, detail=f"Unknown preset: {request.preset}") from exc

        try:
            output = resolve_output_path(request.video, request.output, settings.output_dir)
            result = service.run(request.video, output, preset=preset)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:  # pragma: no cover
            logger.exception("Unhandled API transcription failure: {}", exc)
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        return TranscriptionResponse(
            preset=result.preset,
            source_language=result.source_language,
            target_language=result.target_language,
            detected_language=result.detected_language,
            video=result.video,
            output=result.output,
            subtitle_line_count=result.subtitle_line_count,
            translation_applied=result.translation_applied,
            segments=[
                SegmentResponse(start=segment.start, end=segment.end, text=segment.text)
                for segment in result.transcript.segments
            ],
        )

    return app


app = create_app()
