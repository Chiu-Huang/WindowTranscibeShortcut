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

        keyboard.add_hotkey("ctrl+shift+t", self._on_hotkey)
        while not self._stop_event.is_set():
            time.sleep(0.1)

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

        keyboard.send("ctrl+c")
        time.sleep(0.15)

        win32clipboard.OpenClipboard()
        try:
            if not win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP):
                return None
            files = win32clipboard.GetClipboardData(win32con.CF_HDROP)
            if not files:
                return None
            return Path(files[0]).resolve()
        finally:
            win32clipboard.CloseClipboard()
