from __future__ import annotations

from loguru import logger

from window_transcribe_shortcut.cli import run_cli
from window_transcribe_shortcut.config import settings
from window_transcribe_shortcut.logging_utils import setup_logging


def main() -> int:
    log_file = setup_logging(settings.output_dir / "logs")
    try:
        return run_cli()
    except Exception as exc:
        logger.exception("Failed to process video: {}", exc)
        print(f"Error: {exc}\nSee log for details: {log_file}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
