from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Callable, Optional


class HotkeyMonitor:
    """Listens for Ctrl+Shift+T and emits selected file path from Explorer."""

    def __init__(self, callback: Callable[[Path], None]) -> None:
        self._callback = callback
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def _run(self) -> None:
        try:
            import keyboard
        except ImportError as exc:
            raise RuntimeError("keyboard package is required for hotkey monitor") from exc

        hotkey_id = None
        try:
            hotkey_id = keyboard.add_hotkey("ctrl+shift+t", self._on_hotkey)
            while not self._stop_event.is_set():
                time.sleep(0.1)
        finally:
            if hotkey_id is not None:
                keyboard.remove_hotkey(hotkey_id)

    def _on_hotkey(self) -> None:
        path = self._get_selected_file_from_clipboard()
        if path:
            self._callback(path)

    @staticmethod
    def _get_selected_file_from_clipboard() -> Optional[Path]:
        try:
            import keyboard
            import win32clipboard
            import win32con
        except ImportError:
            return None

        previous_text: str | None = None
        had_text_format = False
        win32clipboard.OpenClipboard()
        try:
            had_text_format = win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT)
            if had_text_format:
                previous_text = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
        except Exception:
            previous_text = None
            had_text_format = False
        finally:
            win32clipboard.CloseClipboard()

        keyboard.send("ctrl+c")
        time.sleep(0.15)

        selected_path: Optional[Path] = None
        win32clipboard.OpenClipboard()
        try:
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP):
                files = win32clipboard.GetClipboardData(win32con.CF_HDROP)
                if files:
                    selected_path = Path(files[0]).resolve()
        finally:
            win32clipboard.CloseClipboard()

        if had_text_format:
            win32clipboard.OpenClipboard()
            try:
                win32clipboard.EmptyClipboard()
                if previous_text is not None:
                    win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, previous_text)
            except Exception:
                pass
            finally:
                win32clipboard.CloseClipboard()

        return selected_path
