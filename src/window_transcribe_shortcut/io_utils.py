from __future__ import annotations

from pathlib import Path


def ensure_video_file(path: Path) -> Path:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Video file not found: {path}")
    return path


def make_output_base(video_path: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / video_path.stem
