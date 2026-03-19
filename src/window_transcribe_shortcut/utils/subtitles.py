from __future__ import annotations

from pathlib import Path

from window_transcribe_shortcut.models import Transcript


def _format_timestamp(seconds: float) -> str:
    total_ms = max(0, int(seconds * 1000))
    ms = total_ms % 1000
    total_s = total_ms // 1000
    s = total_s % 60
    total_m = total_s // 60
    m = total_m % 60
    h = total_m // 60
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'


def write_srt(transcript: Transcript, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for idx, seg in enumerate(transcript.segments, start=1):
        lines.extend(
            [
                str(idx),
                f'{_format_timestamp(seg.start)} --> {_format_timestamp(seg.end)}',
                seg.text.strip(),
                '',
            ]
        )
    output_path.write_text('\n'.join(lines), encoding='utf-8')
