from __future__ import annotations

import threading
from typing import Any
from typing import Callable

try:
    from loguru import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)


class TrayManager:
    """System tray status indicator + notifications."""

    def __init__(self, on_settings: Callable[[], None], on_quit: Callable[[], None]) -> None:
        self._on_settings = on_settings
        self._on_quit = on_quit
        self._icon = None
        self._icons: dict[str, Any] = {}
        self._state_lock = threading.Lock()

    def start(self) -> None:
        try:
            import pystray
            from PIL import Image, ImageDraw
        except ImportError as exc:
            raise RuntimeError("pystray and pillow are required for tray support") from exc

        def create_image(color: str):
            image = Image.new("RGB", (64, 64), "#151515")
            draw = ImageDraw.Draw(image)
            draw.ellipse((12, 12, 52, 52), fill=color)
            return image

        self._icons = {
            "idle": create_image("#3a86ff"),
            "working": create_image("#ffd60a"),
            "error": create_image("#e63946"),
        }

        menu = pystray.Menu(
            pystray.MenuItem("Settings", lambda: self._on_settings()),
            pystray.MenuItem("Quit", lambda: self._on_quit()),
        )

        self._icon = pystray.Icon(
            name="WindowTranscibeShortcut",
            icon=self._icons["idle"],
            title="WindowTranscibeShortcut - Idle",
            menu=menu,
        )

        threading.Thread(target=self._icon.run, daemon=True).start()

    def stop(self) -> None:
        if self._icon:
            self._icon.stop()

    def set_idle(self) -> None:
        self._set_state("idle", "WindowTranscibeShortcut - Idle")

    def set_working(self) -> None:
        self._set_state("working", "WindowTranscibeShortcut - Processing...")

    def set_progress(self, percent: int) -> None:
        bounded = max(0, min(percent, 100))
        self._set_state("working", f"WindowTranscibeShortcut - Processing... {bounded}%")

    def set_error(self) -> None:
        self._set_state("error", "WindowTranscibeShortcut - Error")

    def _set_state(self, state: str, title: str) -> None:
        with self._state_lock:
            if not self._icon or state not in self._icons:
                return
            self._icon.icon = self._icons[state]
            self._icon.title = title

    @staticmethod
    def notify(title: str, message: str) -> None:
        try:
            from plyer import notification

            notification.notify(
                title=title,
                message=message,
                app_name="WindowTranscibeShortcut",
                timeout=5,
            )
            return
        except ImportError:
            logger.warning("plyer not available; falling back to win10toast notifications")
        except Exception as exc:
            logger.warning(f"Failed to send plyer notification: {exc}")

        try:
            from win10toast import ToastNotifier

            toaster = ToastNotifier()
            toaster.show_toast(title, message, duration=5, threaded=True)
        except Exception as exc:
            logger.warning(f"Failed to send fallback Windows notification: {exc}")
