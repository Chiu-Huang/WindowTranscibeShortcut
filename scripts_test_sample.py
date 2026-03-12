"""Manual helper: pick one sample file and run the actual processing route."""

from __future__ import annotations

import random
from pathlib import Path

from window_transcribe_shortcut.main import App, MEDIA_EXTS
from window_transcribe_shortcut.transcriber import Transcriber
from window_transcribe_shortcut.translator import Translator

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

    print(f"Selected sample file: {file_path}")

    translator = Translator()
    if suffix in MEDIA_EXTS:
        print("Route: media -> transcribe+translate")
        transcriber = Transcriber(model_name="tiny")
        result = transcriber.transcribe(file_path)
        segments = result.get("segments", [])
        texts = [seg.get("text", "") for seg in segments]
        translated = translator.translate(texts, hinted_language=result.get("language"))
        out_path = file_path.with_suffix(".zh.srt")
        App._save_segments_as_srt(out_path, segments, translated)
        print(f"Transcribed {len(segments)} segments; wrote {out_path}")
    elif suffix == ".srt":
        print("Route: .srt -> translate")
        rows = App._load_srt(file_path)
        texts = [text for _, text in rows]
        translated = translator.translate(texts)
        out_path = file_path.with_name(f"{file_path.stem}_translated.srt")
        App._save_srt(out_path, rows, translated)
        print(f"Translated {len(rows)} rows; wrote {out_path}")


if __name__ == "__main__":
    main()
