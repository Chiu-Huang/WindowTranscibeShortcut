from __future__ import annotations

import threading
from typing import Callable


class TrayManager:
    """System tray status indicator + notifications."""

    def __init__(self, on_settings: Callable[[], None], on_quit: Callable[[], None]) -> None:
        self._on_settings = on_settings
        self._on_quit = on_quit
        self._icon = None

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

        menu = pystray.Menu(
            pystray.MenuItem("Settings", lambda: self._on_settings()),
            pystray.MenuItem("Quit", lambda: self._on_quit()),
        )

        self._icon = pystray.Icon(
            name="WindowTranscibeShortcut",
            icon=create_image("#3a86ff"),
            title="WindowTranscibeShortcut",
            menu=menu,
        )

        threading.Thread(target=self._icon.run, daemon=True).start()

    def stop(self) -> None:
        if self._icon:
            self._icon.stop()

    def set_idle(self) -> None:
        return

    def set_working(self) -> None:
        return

    def set_error(self) -> None:
        return

    @staticmethod
    def notify(title: str, message: str) -> None:
        try:
            from plyer import notification

            notification.notify(title=title, message=message, app_name="WindowTranscibeShortcut")
        except Exception:
            pass
