from __future__ import annotations

from fastapi import FastAPI, HTTPException
from loguru import logger

from transcribe_service.api_models import (
    HealthResponse,
    ModelInfoResponse,
    SegmentResponse,
    TranscriptionRequest,
    TranscriptionResponse,
    WarmupRequest,
)
from transcribe_service.pipeline import TranscriptionService

service = TranscriptionService()


def _model_response() -> ModelInfoResponse:
    model = service.model_info
    return ModelInfoResponse(
        name=model.name,
        device=model.device,
        compute_type=model.compute_type,
        loaded_language=model.loaded_language,
    )


def create_app() -> FastAPI:
    app = FastAPI(
        title="Transcribe Service",
        version="0.1.0",
        description="ASR-only WhisperX transcription service.",
    )

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            model_loaded=service.is_model_loaded,
            model=_model_response(),
        )

    @app.post("/warmup", response_model=HealthResponse)
    def warmup(request: WarmupRequest) -> HealthResponse:
        logger.info("Warming up WhisperX backend")
        service.preload_model(source_lang=request.source_lang)
        return health()

    @app.post("/transcribe", response_model=TranscriptionResponse)
    def transcribe(request: TranscriptionRequest) -> TranscriptionResponse:
        try:
            result = service.transcribe(request.video, source_lang=request.source_lang)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:  # pragma: no cover
            logger.exception("Unhandled transcription failure: {}", exc)
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        return TranscriptionResponse(
            detected_language=result.transcript.language or request.source_lang or "unknown",
            segments=[
                SegmentResponse(start=segment.start, end=segment.end, text=segment.text)
                for segment in result.transcript.segments
            ],
            model=_model_response(),
            processing_time_seconds=result.processing_time_seconds,
        )

    return app


app = create_app()
