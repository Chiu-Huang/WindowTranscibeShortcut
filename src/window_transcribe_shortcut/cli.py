from __future__ import annotations

import argparse
from pathlib import Path

from loguru import logger

from window_transcribe_shortcut.config import settings
from window_transcribe_shortcut.io_utils import ensure_video_file, make_output_base
from window_transcribe_shortcut.pipeline import TranscriptionService
from window_transcribe_shortcut.presets import DEFAULT_PRESET, PRESETS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Transcribe video and output Chinese subtitles (.srt)")
    parser.add_argument("video", type=Path, help="Path to input video")
    parser.add_argument("--preset", choices=sorted(PRESETS.keys()), default=DEFAULT_PRESET.name)
    parser.add_argument("--output", type=Path, default=None, help="Output .srt path")
    return parser


def run_cli() -> int:
    args = build_parser().parse_args()
    video = ensure_video_file(args.video)
    preset = PRESETS[args.preset]

    output = args.output or make_output_base(video, settings.output_dir).with_suffix(".zh.srt")
    logger.info("Using preset {} ({})", preset.name, preset.description)

    service = TranscriptionService()
    service.run(video, output, source_lang=preset.source_lang, target_lang=preset.target_lang)
    print(f"Done! Subtitle saved to: {output}")
    return 0
