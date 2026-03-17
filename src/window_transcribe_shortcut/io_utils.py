from __future__ import annotations

from pathlib import Path

from loguru import logger


def ensure_output_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def build_output_path(video_path: Path, output_dir: Path) -> Path:
    output_name = f"{video_path.stem}.zh.srt"
    return output_dir / output_name


def save_text(path: Path, text: str) -> None:
    logger.info("Writing subtitle file: {}", path)
    path.write_text(text, encoding="utf-8")
