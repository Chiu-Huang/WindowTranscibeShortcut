from __future__ import annotations

import argparse

import uvicorn
from loguru import logger

from window_transcribe_shortcut.api import app
from window_transcribe_shortcut.config import settings
from window_transcribe_shortcut.utils import setup_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Window Transcribe Shortcut orchestrator API.")
    parser.add_argument("--host", default=settings.api_host, help="Host interface to bind the API server to.")
    parser.add_argument("--port", type=int, default=settings.api_port, help="Port for the API server.")
    parser.add_argument("--reload", action="store_true", help="Enable uvicorn auto-reload for development.")
    parser.add_argument("--debug", action="store_true", help="Enable verbose console logging.")
    parser.add_argument("--warmup", action="store_true", help="Load the transcription model via the transcribe service before accepting requests.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    log_file = setup_logging(settings.output_dir / "logs", debug=args.debug)
    logger.debug("API log file: {}", log_file)

    if args.warmup:
        from window_transcribe_shortcut.api import service

        logger.info("Preloading transcription model through the transcribe service")
        service.preload_model()

    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload, log_config=None)
    return 0
