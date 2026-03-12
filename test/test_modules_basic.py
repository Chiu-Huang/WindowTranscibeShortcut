from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from window_transcribe_shortcut.config_ui import AppConfig, ConfigManager
from window_transcribe_shortcut.main import App
from window_transcribe_shortcut.translator import Translator


class ConfigManagerTests(unittest.TestCase):
    def test_load_creates_default_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "config.json"
            manager = ConfigManager(cfg_path)
            cfg = manager.load()
            self.assertEqual(cfg.whisper_model, "tiny")
            self.assertEqual(cfg.translator_model, "facebook/nllb-200-distilled-600M")
            self.assertTrue(cfg_path.exists())

    def test_save_and_load_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "config.json"
            manager = ConfigManager(cfg_path)
            manager.save(
                AppConfig(
                    whisper_model="base",
                    translator_model="facebook/nllb-200-distilled-600M",
                    require_confirmation=False,
                )
            )
            cfg = manager.load()
            self.assertEqual(cfg.whisper_model, "base")
            self.assertFalse(cfg.require_confirmation)


class TranslatorTests(unittest.TestCase):
    def test_detect_language(self) -> None:
        translator = Translator()
        self.assertEqual(translator.detect_source_language(["你好，世界"]), "zho_Hans")
        self.assertEqual(translator.detect_source_language(["hello world"]), "eng_Latn")
        self.assertEqual(translator.detect_source_language(["こんにちは"]), "jpn_Jpan")

    def test_translate_skips_when_already_chinese(self) -> None:
        translator = Translator()
        src = ["这是中文", "保持原文"]
        out = translator.translate(src)
        self.assertEqual(out, src)


class SrtOutputTests(unittest.TestCase):
    def test_save_srt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.srt"
            rows = [("00:00:01,000 --> 00:00:02,000", "Hello")]
            App._save_srt(out, rows, ["你好"])
            content = out.read_text(encoding="utf-8")
            self.assertIn("00:00:01,000 --> 00:00:02,000", content)
            self.assertIn("你好", content)

    def test_save_segments_as_srt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "segments.srt"
            segments = [{"start": 0.0, "end": 1.2, "text": "hello"}]
            App._save_segments_as_srt(out, segments, ["你好"])
            content = out.read_text(encoding="utf-8")
            self.assertIn("00:00:00,000 --> 00:00:01,200", content)
            self.assertIn("你好", content)


if __name__ == "__main__":
    unittest.main()
