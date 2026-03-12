from __future__ import annotations

from pathlib import Path

from window_transcribe_shortcut.config_ui import AppConfig, ConfigManager
from window_transcribe_shortcut.main import App
from window_transcribe_shortcut.transcriber import Transcriber
from window_transcribe_shortcut.translator import Translator


def test_load_creates_default_config(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.json"
    manager = ConfigManager(cfg_path)

    cfg = manager.load()

    assert cfg.whisper_model == "tiny"
    assert cfg.translator_model == "facebook/nllb-200-distilled-600M"
    assert cfg.require_confirmation is True
    assert cfg_path.exists()


def test_load_recovers_from_corrupt_config(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text("{not-json", encoding="utf-8")
    manager = ConfigManager(cfg_path)

    cfg = manager.load()

    assert cfg == AppConfig()


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.json"
    manager = ConfigManager(cfg_path)

    manager.save(
        AppConfig(
            whisper_model="base",
            translator_model="facebook/nllb-200-distilled-600M",
            require_confirmation=False,
        )
    )

    cfg = manager.load()
    assert cfg.whisper_model == "base"
    assert cfg.require_confirmation is False


def test_detect_language_chinese() -> None:
    translator = Translator()
    detected = translator.detect_source_language(["你好，世界"])

    assert "zho" in detected.lower()


def test_detect_language_english() -> None:
    translator = Translator()
    detected = translator.detect_source_language(["hello world"])

    assert "eng" in detected.lower()


def test_detect_language_japanese() -> None:
    translator = Translator()
    detected = translator.detect_source_language(["こんにちは"])

    assert "jpn" in detected.lower()


def test_translate_skips_when_already_chinese() -> None:
    translator = Translator()
    src = ["这是中文", "保持原文"]

    out = translator.translate(src)

    assert out == src


def test_save_srt(tmp_path: Path) -> None:
    out = tmp_path / "out.srt"
    rows = [("00:00:01,000 --> 00:00:02,000", "Hello")]

    App._save_srt(out, rows, ["你好"])

    assert out.exists(), "SRT file should be created"
    content = out.read_text(encoding="utf-8")
    assert "1\n" in content
    assert "00:00:01,000 --> 00:00:02,000" in content
    assert "你好" in content


def test_save_segments_as_srt(tmp_path: Path) -> None:
    out = tmp_path / "segments.srt"
    segments = [{"start": 0.0, "end": 1.2, "text": "hello"}]

    App._save_segments_as_srt(out, segments, ["你好"])

    assert out.exists(), "SRT file should be created"
    content = out.read_text(encoding="utf-8")
    assert "1\n" in content
    assert "00:00:00,000 --> 00:00:01,200" in content
    assert "你好" in content


def test_transcriber_handles_missing_segments(monkeypatch) -> None:
    class FakeModel:
        def transcribe(self, _: str):
            return {"language": "en"}

    transcriber = Transcriber()
    monkeypatch.setattr(transcriber, "_ensure_model", lambda: FakeModel())
    monkeypatch.setattr(transcriber, "_reset_timer", lambda: None)

    result = transcriber.transcribe(Path("sample.mp4"))

    assert result["language"] == "en"
    assert result["segments"] == []


def test_transcriber_rejects_non_dict_results(monkeypatch) -> None:
    class FakeModel:
        def transcribe(self, _: str):
            return "unexpected"

    transcriber = Transcriber()
    monkeypatch.setattr(transcriber, "_ensure_model", lambda: FakeModel())
    monkeypatch.setattr(transcriber, "_reset_timer", lambda: None)

    import pytest

    with pytest.raises(ValueError, match="Unexpected whisperx result type"):
        transcriber.transcribe(Path("sample.mp4"))


def test_translate_uses_batches(monkeypatch) -> None:
    class FakeTensor:
        def __init__(self) -> None:
            self.is_cuda = False

        def to(self, _: str):
            return self

    class FakeTokenizer:
        def __init__(self) -> None:
            self.src_lang = ""

        def __call__(self, items, **_kwargs):
            return {"input_ids": FakeTensor(), "texts": list(items)}

        def convert_tokens_to_ids(self, _token: str) -> int:
            return 1

        def batch_decode(self, generated, **_kwargs):
            return [f"translated:{item}" for item in generated]

    class FakeModel:
        def __init__(self) -> None:
            self.calls = []

        def parameters(self):
            yield FakeTensor()

        def generate(self, **encoded):
            self.calls.append(list(encoded["texts"]))
            return encoded["texts"]

    translator = Translator()
    model = FakeModel()
    tokenizer = FakeTokenizer()
    monkeypatch.setattr(translator, "_ensure_model", lambda: (model, tokenizer))
    monkeypatch.setattr(translator, "_reset_timer", lambda: None)

    result = translator.translate(["a", "b", "c", "d", "e"], hinted_language="en", batch_size=2)

    assert result == [
        "translated:a",
        "translated:b",
        "translated:c",
        "translated:d",
        "translated:e",
    ]
    assert model.calls == [["a", "b"], ["c", "d"], ["e"]]
