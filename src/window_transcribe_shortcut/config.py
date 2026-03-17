from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    deepl_api_key: str | None = Field(default=None, alias="DEEPL_API_KEY")
    deepl_base_url: str = Field(default="https://api-free.deepl.com/v2", alias="DEEPL_BASE_URL")
    whisper_model: str = Field(default="small", alias="WHISPER_MODEL")
    device: str = Field(default="cpu", alias="WHISPER_DEVICE")
    compute_type: str = Field(default="int8", alias="WHISPER_COMPUTE_TYPE")
    output_dir: Path = Field(default=Path("outputs"), alias="OUTPUT_DIR")


settings = Settings()
