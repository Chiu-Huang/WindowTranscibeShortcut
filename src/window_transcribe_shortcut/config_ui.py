from __future__ import annotations

import json
import os
import re
import threading
from dataclasses import asdict, dataclass
from pathlib import Path
from threading import Lock
from typing import Callable, Optional


def get_config_dir() -> Path:
    """Get a stable per-user config directory across platforms."""
    if os.name == "nt":
        base = Path(os.getenv("APPDATA", "~")).expanduser()
    elif os.name == "darwin":
        base = Path("~/Library/Application Support").expanduser()
    else:
        base = Path(os.getenv("XDG_CONFIG_HOME", "~/.config")).expanduser()

    config_dir = base / "WindowTranscibeShortcut"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


CONFIG_PATH = get_config_dir() / "config.json"


@dataclass
class AppConfig:
    whisper_model: str = "tiny"
    translator_model: str = "facebook/nllb-200-distilled-600M"
    require_confirmation: bool = True


class ConfigManager:
    """Thread-safe config loader/saver backed by config.json."""

    def __init__(self, path: Path = CONFIG_PATH) -> None:
        self._path = path
        self._lock = Lock()

    def load(self) -> AppConfig:
        with self._lock:
            if not self._path.exists():
                config = AppConfig()
                self._write_unlocked(config)
                return config

            try:
                with self._path.open("r", encoding="utf-8") as fp:
                    data = json.load(fp)
            except (json.JSONDecodeError, OSError, TypeError):
                config = AppConfig()
                self._write_unlocked(config)
                return config

            return AppConfig(
                whisper_model=data.get("whisper_model", AppConfig.whisper_model),
                translator_model=data.get("translator_model", AppConfig.translator_model),
                require_confirmation=bool(
                    data.get("require_confirmation", AppConfig.require_confirmation)
                ),
            )

    def save(self, config: AppConfig) -> None:
        with self._lock:
            self._write_unlocked(config)

    def _write_unlocked(self, config: AppConfig) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as fp:
            json.dump(asdict(config), fp, indent=2, ensure_ascii=False)


class SettingsUI:
    """Flet-based settings editor."""

    def __init__(self, config_manager: ConfigManager) -> None:
        self._config_manager = config_manager

    def open(self, on_saved: Optional[Callable[[AppConfig], None]] = None) -> None:
        threading.Thread(target=self._open_ui, args=(on_saved,), daemon=True).start()

    def _open_ui(self, on_saved: Optional[Callable[[AppConfig], None]] = None) -> None:
        try:
            import flet as ft
        except ImportError as exc:
            raise RuntimeError("flet is required to open Settings UI.") from exc

        config = self._config_manager.load()
        model_pattern = re.compile(r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$")

        def app(page: "ft.Page") -> None:
            page.title = "WindowTranscibeShortcut Settings"
            page.theme_mode = ft.ThemeMode.DARK
            page.window_width = 560
            page.window_height = 360

            whisper = ft.Dropdown(
                label="Whisper model",
                value=config.whisper_model,
                options=[
                    ft.dropdown.Option(k)
                    for k in ["tiny", "base", "small", "medium", "large-v3"]
                ],
            )
            translator = ft.TextField(
                label="Translator model",
                value=config.translator_model,
                hint_text="facebook/nllb-200-distilled-600M",
            )
            confirm = ft.Switch(
                label="Require confirmation before processing",
                value=config.require_confirmation,
            )
            status = ft.Text(value="")

            def on_save(_):
                translator_value = (translator.value or "").strip()
                if translator_value and not model_pattern.match(translator_value):
                    status.value = "❌ Invalid model name (expected 'org/model')"
                    status.color = "red"
                    page.update()
                    return

                new_cfg = AppConfig(
                    whisper_model=whisper.value or AppConfig.whisper_model,
                    translator_model=translator_value or AppConfig.translator_model,
                    require_confirmation=bool(confirm.value),
                )
                self._config_manager.save(new_cfg)

                if new_cfg.whisper_model != config.whisper_model:
                    status.value = f"✓ Saved! First run will download: {new_cfg.whisper_model}"
                else:
                    status.value = "✓ Saved successfully!"
                status.color = "green"
                page.update()
                if on_saved:
                    on_saved(new_cfg)

                def close_after_delay() -> None:
                    import time

                    time.sleep(1.2)
                    page.window_close()

                threading.Thread(target=close_after_delay, daemon=True).start()

            page.add(
                ft.Column(
                    controls=[
                        ft.Text("Settings", size=28, weight=ft.FontWeight.BOLD),
                        whisper,
                        translator,
                        confirm,
                        ft.Row([ft.ElevatedButton("Save", on_click=on_save), status]),
                    ]
                )
            )

        ft.app(target=app)
