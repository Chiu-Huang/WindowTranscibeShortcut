from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Application configuration loaded from environment variables."""

    deepl_api_key: str = ""
    whisper_model: str = "tiny"
    whisper_device: str = "cpu"
    output_dir: Path = Path("output")
    source_lang_default: str = "en"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="WTS_",
        extra="ignore",
    )


settings = AppSettings()
