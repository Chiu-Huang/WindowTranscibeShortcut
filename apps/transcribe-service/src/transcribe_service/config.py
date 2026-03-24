from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


APP_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = APP_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    whisper_model: str = Field(default="small", alias="WHISPER_MODEL")
    device: str = Field(default="cpu", alias="WHISPER_DEVICE")
    compute_type: str = Field(default="int8", alias="WHISPER_COMPUTE_TYPE")
    api_host: str = Field(default="127.0.0.1", alias="TRANSCRIBE_API_HOST")
    api_port: int = Field(default=8766, alias="TRANSCRIBE_API_PORT")


settings = Settings()
