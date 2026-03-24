from __future__ import annotations

from loguru import logger

from window_transcribe_shortcut.cli import build_parser, run_cli
from window_transcribe_shortcut.config import settings
from window_transcribe_shortcut.utils import setup_logging


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    log_file = setup_logging(settings.output_dir / "logs", debug=args.debug)
    logger.debug("Log file: {}", log_file)
    try:
        return run_cli(args)
    except Exception as exc:
        logger.exception("Failed to process video: {}", exc)
        print(f"Error: {exc}\nSee log for details: {log_file}")
        return 1
