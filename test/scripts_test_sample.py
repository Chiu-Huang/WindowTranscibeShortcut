"""Small manual test helper that picks one file from ./sample and routes by extension."""

from __future__ import annotations

import random
from pathlib import Path

MEDIA_EXTS = {".mp3", ".wav", ".m4a", ".mp4", ".mkv", ".mov", ".flac"}
SUPPORTED_EXTS = MEDIA_EXTS | {".srt"}


def pick_sample_file(sample_dir: Path) -> Path:
    files = [
        p
        for p in sample_dir.iterdir()
        if p.is_file() and not p.name.startswith(".") and p.suffix.lower() in SUPPORTED_EXTS
    ]
    if not files:
        raise FileNotFoundError(
            "No supported files in sample/. Add one .srt or media file and rerun."
        )
    return random.choice(files)


def main() -> None:
    sample_dir = Path("sample")
    file_path = pick_sample_file(sample_dir)
    suffix = file_path.suffix.lower()
    route = "media -> transcribe+translate" if suffix in MEDIA_EXTS else ".srt -> translate"
    print(f"Selected sample file: {file_path}")
    print(f"Detected route: {route}")


if __name__ == "__main__":
    main()
