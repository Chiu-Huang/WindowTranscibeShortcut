from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[4]
ENV_FILE = ROOT_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    output_dir: Path = Field(default=Path("outputs"), alias="OUTPUT_DIR")
    api_host: str = Field(default="127.0.0.1", alias="API_HOST")
    api_port: int = Field(default=8765, alias="API_PORT")
    transcribe_service_url: str = Field(
        default="http://127.0.0.1:8766",
        alias="TRANSCRIBE_SERVICE_URL",
    )
    translation_service_url: str = Field(
        default="http://127.0.0.1:8876",
        alias="TRANSLATION_SERVICE_URL",
    )
    service_request_timeout_seconds: float = Field(
        default=300.0,
        alias="SERVICE_REQUEST_TIMEOUT_SECONDS",
    )


settings = Settings()
