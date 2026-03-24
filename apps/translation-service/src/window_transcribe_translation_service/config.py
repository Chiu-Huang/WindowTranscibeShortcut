from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


APP_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = APP_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    model_name: str = Field(default="facebook/nllb-200-distilled-600M", alias="TRANSLATION_MODEL")
    device: str = Field(default="auto", alias="TRANSLATION_DEVICE")
    torch_dtype: str = Field(default="auto", alias="TRANSLATION_TORCH_DTYPE")
    max_batch_size: int = Field(default=8, alias="TRANSLATION_MAX_BATCH_SIZE")
    api_host: str = Field(default="127.0.0.1", alias="TRANSLATION_API_HOST")
    api_port: int = Field(default=8876, alias="TRANSLATION_API_PORT")


settings = Settings()
