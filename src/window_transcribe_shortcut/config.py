from __future__ import annotations

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Application configuration loaded from environment variables."""

    deepl_api_key: str = ""
    whisper_model: str = "tiny"
    whisper_model_path: Path | None = None
    whisper_device: str = "cpu"
    output_dir: Path = Path("output")
    source_lang_default: str = "en"

    @field_validator("whisper_model_path", mode="before")
    @classmethod
    def empty_model_path_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="WTS_",
        extra="ignore",
    )


settings = AppSettings()
