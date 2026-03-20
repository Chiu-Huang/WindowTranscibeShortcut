from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[4]
ENV_FILE = ROOT_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    deepl_api_key: str | None = Field(default=None, alias="DEEPL_API_KEY")
    deepl_base_url: str = Field(default="https://api-free.deepl.com/v2", alias="DEEPL_BASE_URL")
    local_translation_enabled: bool = Field(default=False, alias="LOCAL_TRANSLATION_ENABLED")
    local_translation_url: str = Field(
        default="http://127.0.0.1:9988/translate",
        alias="LOCAL_TRANSLATION_URL",
    )
    translation_request_timeout_seconds: float = Field(
        default=60.0,
        alias="TRANSLATION_REQUEST_TIMEOUT_SECONDS",
    )
    api_host: str = Field(default="127.0.0.1", alias="TRANSLATION_API_HOST")
    api_port: int = Field(default=8876, alias="TRANSLATION_API_PORT")


settings = Settings()
