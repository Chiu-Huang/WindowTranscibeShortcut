from __future__ import annotations

from fastapi import FastAPI, HTTPException
from loguru import logger

from window_transcribe_translation_service.api_models import (
    HealthResponse,
    TranslationRequest,
    TranslationResponse,
)
from window_transcribe_translation_service.config import settings
from window_transcribe_translation_service.pipeline import TranslationService

service = TranslationService()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Window Transcribe Translation Service",
        version="0.1.0",
        description="Translation-only service wrapping the configured translation backends.",
    )

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            deepl_configured=bool(settings.deepl_api_key and settings.deepl_api_key != "your_deepl_api_key"),
            local_translation_enabled=settings.local_translation_enabled,
        )

    @app.post("/translate", response_model=TranslationResponse)
    def translate(request: TranslationRequest) -> TranslationResponse:
        try:
            translations = service.translate_lines(
                request.lines,
                source_lang=request.source_lang,
                target_lang=request.target_lang,
            )
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:  # pragma: no cover
            logger.exception("Unhandled translation failure: {}", exc)
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return TranslationResponse(translations=translations)

    return app


app = create_app()
