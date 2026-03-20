from __future__ import annotations

from pathlib import Path

DEFAULT_SUBTITLE_SUFFIX = ".srt"


def ensure_video_file(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.exists() or not resolved.is_file():
        raise FileNotFoundError(f"Video file not found: {resolved}")
    return resolved


def build_output_base(video_path: Path, output_dir: Path) -> Path:
    resolved_output_dir = output_dir.expanduser().resolve()
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    return resolved_output_dir / video_path.stem


def resolve_output_path(video_path: Path, output: Path | None, output_dir: Path) -> Path:
    resolved_video = video_path.expanduser().resolve()
    if output is None:
        return build_output_base(resolved_video, output_dir).with_suffix(DEFAULT_SUBTITLE_SUFFIX)

    resolved_output = output.expanduser().resolve()
    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    return resolved_output
