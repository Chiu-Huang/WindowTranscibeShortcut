from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import srt

from window_transcribe_shortcut.models import Transcript


def write_srt(transcript: Transcript, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    subtitles = [
        srt.Subtitle(
            index=index,
            start=timedelta(seconds=segment.start),
            end=timedelta(seconds=segment.end),
            content=segment.text.strip(),
        )
        for index, segment in enumerate(transcript.segments, start=1)
    ]
    output_path.write_text(srt.compose(subtitles), encoding="utf-8")
