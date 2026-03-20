from __future__ import annotations

import argparse

import uvicorn

from transcribe_service.api import app
from transcribe_service.config import settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the WhisperX transcription service API.")
    parser.add_argument("--host", default=settings.api_host, help="Host interface to bind the API server to.")
    parser.add_argument("--port", type=int, default=settings.api_port, help="Port for the API server.")
    parser.add_argument("--reload", action="store_true", help="Enable uvicorn auto-reload for development.")
    parser.add_argument("--warmup", action="store_true", help="Load the WhisperX model before accepting requests.")
    parser.add_argument("--source-lang", default=None, help="Optional language hint to preload the model with.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.warmup:
        from transcribe_service.api import service

        service.preload_model(source_lang=args.source_lang)

    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload, log_config=None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
