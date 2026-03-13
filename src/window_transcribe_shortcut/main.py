from __future__ import annotations

import ctypes
import threading
import time
from pathlib import Path
from typing import List, Tuple

try:
    from loguru import logger
except ImportError:
    import logging

    logger = logging.getLogger("window_transcribe_shortcut")
    if not logger.handlers:
        logging.basicConfig(level=logging.INFO)

from .config_ui import AppConfig, ConfigManager, SettingsUI
from .monitor import HotkeyMonitor
from .transcriber import Transcriber
from .translator import Translator
from .tray_manager import TrayManager

MEDIA_EXTS = {".mp3", ".wav", ".m4a", ".mp4", ".mkv", ".mov", ".flac"}


class App:
    def __init__(self) -> None:
        self.config_manager = ConfigManager()
        cfg = self.config_manager.load()
        self.transcriber = Transcriber(model_name=cfg.whisper_model)
        self.translator = Translator(model_name=cfg.translator_model)
        self.monitor = HotkeyMonitor(self._on_file_selected)
        self.tray = TrayManager(on_settings=self._open_settings, on_quit=self.stop)
        self._shutdown = threading.Event()
        self._service_lock = threading.RLock()

    def start(self) -> None:
        self.tray.start()
        self.monitor.start()
        self.tray.notify("WindowTranscibeShortcut", "Running in background")
        logger.info("Application started")
        self._shutdown.wait()

    def stop(self) -> None:
        self._shutdown.set()
        self.monitor.stop()
        self.tray.stop()
        self.transcriber.unload()
        self.translator.unload()

    def _open_settings(self) -> None:
        proc = SettingsUI.open_in_subprocess()

        def wait_and_reload() -> None:
            proc.wait()
            try:
                self._on_config_saved(self.config_manager.load())
            except Exception:
                logger.exception("Failed to reload configuration after settings UI closed")

        threading.Thread(target=wait_and_reload, daemon=True).start()

    def _on_config_saved(self, config: AppConfig) -> None:
        with self._service_lock:
            old_transcriber = self.transcriber
            old_translator = self.translator
            self.transcriber = Transcriber(model_name=config.whisper_model)
            self.translator = Translator(model_name=config.translator_model)

        threading.Thread(
            target=self._unload_models,
            args=(old_transcriber, old_translator),
            daemon=True,
        ).start()

    def _on_file_selected(self, path: Path) -> None:
        cfg = self.config_manager.load()
        if cfg.require_confirmation:
            threading.Thread(target=self._confirm_and_process, args=(path,), daemon=True).start()
            return
        threading.Thread(target=self._process_file, args=(path,), daemon=True).start()

    def _confirm_and_process(self, path: Path) -> None:
        if self._confirm(path):
            self._process_file(path)

    @staticmethod
    def _confirm(path: Path) -> bool:
        msg = f"Process this file?\n\n{path}"
        result = ctypes.windll.user32.MessageBoxW(0, msg, "WindowTranscibeShortcut", 0x4)
        return result == 6

    def _process_file(self, path: Path) -> None:
        try:
            self.tray.set_working()
            suffix = path.suffix.lower()
            started_at = time.perf_counter()
            with self._service_lock:
                transcriber = self.transcriber
                translator = self.translator

            if suffix == ".srt":
                rows = self._load_srt(path)
                texts = [text for _, text in rows]
                translated = translator.translate(texts)
                self._save_srt(path.with_name(f"{path.stem}_translated.srt"), rows, translated)
            elif suffix in MEDIA_EXTS:
                progress_state = {"last": -1}

                def on_progress(current: int, total: int) -> None:
                    percent = int(current * 100 / max(total, 1))
                    if percent == progress_state["last"]:
                        return
                    progress_state["last"] = percent
                    self.tray.set_progress(percent)

                result = transcriber.transcribe(path, progress_callback=on_progress)
                segments = result["segments"]
                source_lang = result.get("language")
                texts = [seg.get("text", "") for seg in segments]
                translated = translator.translate(texts, hinted_language=source_lang)
                self._save_segments_as_srt(path.with_suffix(".zh.srt"), segments, translated)
            else:
                raise ValueError(f"Unsupported file type: {path.suffix}")

            self.tray.set_idle()
            elapsed = time.perf_counter() - started_at
            logger.info(f"Finished processing {path.name} in {elapsed:.1f}s")
            self.tray.notify("Transcription completed", f"Finished: {path.name}")
        except (ValueError, RuntimeError, OSError) as exc:
            logger.exception(f"Processing failed for {path}")
            self.tray.set_error()
            self.tray.notify(
                "Processing failed",
                f"{path.name}: file may be unsupported or damaged.",
            )
        except Exception:
            logger.exception(f"Unexpected error while processing {path}")
            self.tray.set_error()
            self.tray.notify("Unexpected error", "Please check the application log for details.")

    @staticmethod
    def _unload_models(transcriber: Transcriber, translator: Translator) -> None:
        transcriber.unload()
        translator.unload()

    @staticmethod
    def _load_srt(path: Path) -> List[Tuple[str, str]]:
        import pysrt

        subs = pysrt.open(str(path), encoding="utf-8")
        return [(f"{item.start} --> {item.end}", item.text) for item in subs]

    @staticmethod
    def _save_srt(out_path: Path, rows: List[Tuple[str, str]], translated: List[str]) -> None:
        with out_path.open("w", encoding="utf-8") as fp:
            for idx, ((time_range, _), text) in enumerate(zip(rows, translated), start=1):
                fp.write(f"{idx}\n{time_range}\n{text}\n\n")

    @staticmethod
    def _save_segments_as_srt(out_path: Path, segments: List[dict], translated: List[str]) -> None:
        def to_srt_time(seconds: float) -> str:
            ms = int(seconds * 1000)
            hh, ms = divmod(ms, 3600000)
            mm, ms = divmod(ms, 60000)
            ss, ms = divmod(ms, 1000)
            return f"{hh:02}:{mm:02}:{ss:02},{ms:03}"

        with out_path.open("w", encoding="utf-8") as fp:
            for idx, (seg, text) in enumerate(zip(segments, translated), start=1):
                start = to_srt_time(float(seg.get("start", 0.0)))
                end = to_srt_time(float(seg.get("end", 0.0)))
                fp.write(f"{idx}\n{start} --> {end}\n{text}\n\n")


def main() -> None:
    App().start()


if __name__ == "__main__":
    main()
