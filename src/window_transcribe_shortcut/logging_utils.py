from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger


def setup_logging(log_dir: Path) -> Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "window_transcribe_shortcut.log"

    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add(
        log_path,
        level="DEBUG",
        rotation="5 MB",
        retention=5,
        enqueue=True,
    )
    return log_path
