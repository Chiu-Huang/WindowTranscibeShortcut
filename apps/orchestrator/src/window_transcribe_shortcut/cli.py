from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from loguru import logger

from window_transcribe_shortcut.config import settings
from window_transcribe_shortcut.pipeline import TranscriptionService
from window_transcribe_shortcut.presets import DEFAULT_PRESET, PRESETS, Preset
from window_transcribe_shortcut.utils import resolve_output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Transcribe video and output Chinese subtitles (.srt)",
        epilog="Example: window-transcribe-shortcut ./video.mp4 --preset ja2zh --debug",
    )
    parser.add_argument("video", type=Path, nargs="?", help="Path to input video")
    parser.add_argument("--preset", choices=sorted(PRESETS.keys()), default=DEFAULT_PRESET.name)
    parser.add_argument("--output", type=Path, default=None, help="Output .srt path")
    parser.add_argument("--debug", action="store_true", help="Enable verbose console logging")
    parser.add_argument("--list-presets", action="store_true", help="Show available presets and exit")
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Print the effective runtime configuration and exit",
    )
    return parser


def _format_preset(preset: Preset) -> str:
    source = preset.source_lang or "auto"
    return f"{preset.name}: {source} -> {preset.target_lang} ({preset.description})"


def _show_presets() -> None:
    print("Available presets:")
    for preset in PRESETS.values():
        print(f"  - {_format_preset(preset)}")


def _show_config() -> None:
    config = settings.model_dump(mode="json", by_alias=True)
    print(json.dumps(config, indent=2, sort_keys=True, ensure_ascii=False))


def _validate_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if args.list_presets or args.show_config:
        return
    if args.video is None:
        parser.error("the following arguments are required: video")


def run_cli(args: argparse.Namespace | None = None) -> int:
    parser = build_parser()
    parsed_args = parser.parse_args() if args is None else args
    _validate_args(parsed_args, parser)

    if parsed_args.list_presets:
        _show_presets()
        return 0

    if parsed_args.show_config:
        _show_config()
        return 0

    preset = PRESETS[parsed_args.preset]
    output = resolve_output_path(parsed_args.video, parsed_args.output, settings.output_dir)

    logger.info("Using preset {} ({})", preset.name, preset.description)
    logger.debug("Effective run arguments: {}", asdict(preset))
    logger.debug("Video input: {}", parsed_args.video)
    logger.debug("Subtitle output: {}", output)

    service = TranscriptionService()
    result = service.run(parsed_args.video, output, preset=preset)
    print(f"Done! Subtitle saved to: {result.output}")
    return 0
