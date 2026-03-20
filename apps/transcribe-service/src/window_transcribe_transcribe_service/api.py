from __future__ import annotations

from fastapi import FastAPI, HTTPException
from loguru import logger

from window_transcribe_transcribe_service.api_models import (
    HealthResponse,
    SegmentResponse,
    TranscriptionRequest,
    TranscriptionResponse,
    WarmupRequest,
)
from window_transcribe_transcribe_service.config import settings
from window_transcribe_transcribe_service.pipeline import TranscriptionService

service = TranscriptionService()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Window Transcribe Transcribe Service",
        version="0.1.0",
        description="WhisperX-only transcription service.",
    )

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            model_loaded=service.is_model_loaded,
            model_name=settings.whisper_model,
            device=settings.device,
        )

    @app.post("/warmup", response_model=HealthResponse)
    def warmup(request: WarmupRequest) -> HealthResponse:
        logger.info("Warming up WhisperX backend")
        service.preload_model(source_lang=request.source_lang)
        return health()

    @app.post("/transcribe", response_model=TranscriptionResponse)
    def transcribe(request: TranscriptionRequest) -> TranscriptionResponse:
        try:
            transcript = service.transcribe(request.video.expanduser().resolve(), source_lang=request.source_lang)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:  # pragma: no cover
            logger.exception("Unhandled transcription failure: {}", exc)
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        return TranscriptionResponse(
            detected_language=transcript.language or request.source_lang or "unknown",
            subtitle_line_count=len(transcript.segments),
            segments=[
                SegmentResponse(start=segment.start, end=segment.end, text=segment.text)
                for segment in transcript.segments
            ],
        )

    return app


app = create_app()
