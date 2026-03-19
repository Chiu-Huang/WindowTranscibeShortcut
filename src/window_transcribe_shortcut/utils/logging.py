from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger


def setup_logging(log_dir: Path, *, debug: bool = False) -> Path:
    resolved_log_dir = log_dir.expanduser().resolve()
    resolved_log_dir.mkdir(parents=True, exist_ok=True)
    log_path = resolved_log_dir / 'window_transcribe_shortcut.log'

    logger.remove()
    logger.add(sys.stderr, level='DEBUG' if debug else 'INFO')
    logger.add(
        log_path,
        level='DEBUG',
        rotation='5 MB',
        retention=5,
        enqueue=True,
        backtrace=debug,
        diagnose=debug,
    )
    return log_path
