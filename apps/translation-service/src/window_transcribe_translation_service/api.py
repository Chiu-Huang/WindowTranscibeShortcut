from __future__ import annotations

from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger

from window_transcribe_translation_service.api_models import (
    HealthResponse,
    ProviderFailureResponse,
    ProviderInfoResponse,
    ProvidersResponse,
    TranslationErrorResponse,
    TranslationRequest,
    TranslationResponse,
)
from window_transcribe_translation_service.pipeline import TranslationService
from window_transcribe_translation_service.providers import TranslationProviderError, TranslationServiceError

service = TranslationService()


def _provider_failures(failures: list[object]) -> list[ProviderFailureResponse]:
    return [ProviderFailureResponse(**asdict(failure)) for failure in failures]


def _provider_info_rows(rows: list[dict[str, object]]) -> list[ProviderInfoResponse]:
    return [ProviderInfoResponse(**row) for row in rows]


def create_app() -> FastAPI:
    app = FastAPI(
        title="Window Transcribe Translation Service",
        version="0.1.0",
        description="Translation-only service backed by a local Transformers/Torch model.",
    )

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        provider_order, providers, engine = service.health_summary()
        return HealthResponse(
            status=engine["status"],
            provider_order=provider_order,
            providers=_provider_info_rows(providers),
            model=str(engine["model"]),
            device=str(engine["device"]),
            loaded=bool(engine["loaded"]),
        )

    @app.get("/providers", response_model=ProvidersResponse)
    def providers() -> ProvidersResponse:
        return ProvidersResponse(providers=_provider_info_rows(service.list_providers()))

    @app.post("/warmup")
    def warmup() -> dict[str, object]:
        return service.warmup()

    @app.post("/translate", response_model=TranslationResponse)
    def translate(request: TranslationRequest):
        try:
            if request.segments is not None:
                attempt, translated_segments = service.translate_segments(
                    request.segments,
                    source_lang=request.source_lang,
                    target_lang=request.target_lang,
                    provider=request.provider,
                )
                return TranslationResponse(
                    provider=attempt.provider,
                    translations=attempt.translations,
                    segments=translated_segments,
                    failures=_provider_failures(attempt.failures),
                )

            attempt = service.translate_lines(
                request.lines or [],
                source_lang=request.source_lang,
                target_lang=request.target_lang,
                provider=request.provider,
            )
            return TranslationResponse(
                provider=attempt.provider,
                translations=attempt.translations,
                failures=_provider_failures(attempt.failures),
            )
        except HTTPException as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content=TranslationErrorResponse(error=str(exc.detail)).model_dump(),
            )
        except TranslationProviderError as exc:
            return JSONResponse(
                status_code=502,
                content=TranslationErrorResponse(
                    error=str(exc),
                    failures=_provider_failures([exc.to_failure()]),
                ).model_dump(),
            )
        except TranslationServiceError as exc:
            return JSONResponse(
                status_code=502,
                content=TranslationErrorResponse(
                    error=str(exc),
                    failures=_provider_failures(exc.failures),
                ).model_dump(),
            )
        except Exception as exc:  # pragma: no cover
            logger.exception("Unhandled translation failure: {}", exc)
            return JSONResponse(
                status_code=500,
                content=TranslationErrorResponse(error=str(exc)).model_dump(),
            )

    return app


app = create_app()
