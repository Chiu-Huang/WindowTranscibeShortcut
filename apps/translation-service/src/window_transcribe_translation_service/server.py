from __future__ import annotations

import argparse
import logging

import uvicorn

from window_transcribe_translation_service.api import app, service
from window_transcribe_translation_service.config import settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the translation service API.")
    parser.add_argument("--host", default=settings.api_host, help="Host interface to bind the API server to.")
    parser.add_argument("--port", type=int, default=settings.api_port, help="Port for the API server.")
    parser.add_argument("--reload", action="store_true", help="Enable uvicorn auto-reload for development.")
    parser.add_argument("--warmup", action="store_true", help="Load the translation model before serving requests.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    if args.warmup:
        service.warmup()
    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)
    return 0
