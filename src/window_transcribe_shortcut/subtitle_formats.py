from __future__ import annotations

from window_transcribe_shortcut.asr.base import TranscriptSegment


def _fmt_srt_time(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    hours = ms // 3_600_000
    ms %= 3_600_000
    minutes = ms // 60_000
    ms %= 60_000
    secs = ms // 1000
    millis = ms % 1000
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def to_srt(segments: list[TranscriptSegment]) -> str:
    lines: list[str] = []
    for idx, seg in enumerate(segments, start=1):
        lines.append(str(idx))
        lines.append(f"{_fmt_srt_time(seg.start)} --> {_fmt_srt_time(seg.end)}")
        lines.append(seg.text)
        lines.append("")
    return "\n".join(lines).strip() + "\n"
