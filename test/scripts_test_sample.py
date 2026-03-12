"""Pytest coverage for sample-file routing helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

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
    return sorted(files)[0]


def process_sample_file(path: Path, transcriber, translator) -> tuple[str, list[str]]:
    suffix = path.suffix.lower()

    if suffix in MEDIA_EXTS:
        result = transcriber.transcribe(path)
        texts = [seg.get("text", "") for seg in result.get("segments", [])]
        translated = translator.translate(texts, hinted_language=result.get("language"))
        return "media -> transcribe+translate", translated

    if suffix == ".srt":
        content = path.read_text(encoding="utf-8")
        translated = translator.translate([content])
        return ".srt -> translate", translated

    raise ValueError(f"Unsupported file type: {path.suffix}")


class _FakeTranscriber:
    def transcribe(self, _path: Path) -> dict:
        return {
            "language": "eng_Latn",
            "segments": [{"text": "hello"}, {"text": "world"}],
        }


class _FakeTranslator:
    def translate(self, texts: list[str], hinted_language: str | None = None) -> list[str]:
        _ = hinted_language
        return [f"zh:{t}" for t in texts]


def test_pick_sample_file_raises_when_empty(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        pick_sample_file(tmp_path)


def test_pick_sample_file_ignores_hidden_and_unsupported(tmp_path: Path) -> None:
    (tmp_path / ".hidden.srt").write_text("ignored", encoding="utf-8")
    (tmp_path / "note.txt").write_text("ignored", encoding="utf-8")
    media = tmp_path / "sample.mp4"
    media.write_text("fake", encoding="utf-8")

    picked = pick_sample_file(tmp_path)

    assert picked == media


def test_process_sample_file_media_route(tmp_path: Path) -> None:
    media = tmp_path / "sample.mp4"
    media.write_text("fake", encoding="utf-8")

    route, translated = process_sample_file(media, _FakeTranscriber(), _FakeTranslator())

    assert route == "media -> transcribe+translate"
    assert translated == ["zh:hello", "zh:world"]


def test_process_sample_file_srt_route(tmp_path: Path) -> None:
    srt = tmp_path / "sample.srt"
    srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nhello\n", encoding="utf-8")

    route, translated = process_sample_file(srt, _FakeTranscriber(), _FakeTranslator())

    assert route == ".srt -> translate"
    assert len(translated) == 1
    assert translated[0].startswith("zh:")
