from __future__ import annotations

import argparse
from pathlib import Path

from loguru import logger

from window_transcribe_shortcut.config import settings
from window_transcribe_shortcut.pipeline import run_pipeline
from window_transcribe_shortcut.presets.profiles import DEFAULT_PRESET_KEY, PRESETS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Transcribe any video and output Chinese subtitles.")
    parser.add_argument("video", type=Path, help="Path to input video/audio file")
    parser.add_argument("--preset", choices=sorted(PRESETS), default=DEFAULT_PRESET_KEY)
    parser.add_argument("--source-lang", default=None, help="Override source language code (en/ja/zh/...) ")
    return parser


def run_cli(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    log_path = Path("transcribe_error.log")
    logger.remove()
    logger.add(lambda msg: print(msg, end=""))
    logger.add(log_path, level="ERROR", rotation="1 MB")

    if not args.video.exists():
        parser.error(f"Input file not found: {args.video}")

    preset = PRESETS[args.preset]
    source_lang = args.source_lang or preset.source_language or settings.source_lang_default

    try:
        output = run_pipeline(video_path=str(args.video), source_language=source_lang, target_language=preset.target_language)
        logger.info("Done. Subtitle created at: {}", output)
        return 0
    except Exception as exc:  # noqa: BLE001
        logger.exception("Processing failed: {}", exc)
        print(f"\nError: {exc}\nSee log file: {log_path.resolve()}")
        try:
            input("Press Enter to exit...")
        except EOFError:
            pass
        return 1
